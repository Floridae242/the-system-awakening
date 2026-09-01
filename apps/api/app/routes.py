import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .achievements import evaluate_achievements
from .auth import create_access_token, current_player
from .config import settings
from .database import get_session
from .game_engine import calculate_quest_reward, chest_rarity_from_roll, level_from_exp
from .models import (
    AuditEvent,
    Chest,
    ChestOpenResult,
    IdempotencyRecord,
    InventoryItem,
    ItemDefinition,
    PlayerProfile,
    PlayerQuest,
    ProgressionLedger,
    QuestDefinition,
    RewardGrant,
    Submission,
    User,
    VerificationResult,
)

router = APIRouter(prefix="/api/v1")


class DemoLogin(BaseModel):
    handle: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")


class ManualEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_minutes: float | None = Field(default=None, ge=0, le=1440)
    distance_km: float | None = Field(default=None, ge=0, le=1000)
    completion: bool | None = None


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_\- ]+$")


class SubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_type: str = Field(pattern=r"^manual$")
    manual_evidence: ManualEvidence = Field(default_factory=ManualEvidence)


@dataclass(frozen=True)
class QuestRules:
    difficulty: str
    primary_stat: str
    objective: dict
    rules_version: str


def quest_snapshot(quest: QuestDefinition) -> dict:
    return {
        "definition_id": quest.id,
        "version": quest.version,
        "difficulty": quest.difficulty,
        "primary_stat": quest.primary_stat,
        "objective": quest.objective,
        "verification_policy": quest.verification_policy,
        "reward_profile": quest.reward_profile,
        "rules_version": "1.0.0",
    }


def accepted_rules(accepted: PlayerQuest) -> QuestRules:
    snapshot = accepted.definition_snapshot
    return QuestRules(
        difficulty=snapshot["difficulty"],
        primary_stat=snapshot["primary_stat"],
        objective=snapshot["objective"],
        rules_version=snapshot.get("rules_version", "1.0.0"),
    )


def envelope(data: object) -> dict:
    return {"success": True, "data": data}


def request_hash(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def player_data(player: PlayerProfile) -> dict:
    return {
        "id": player.id,
        "display_name": player.display_name,
        "level": player.level,
        "current_xp": player.current_xp,
        "streak_days": player.streak_days,
        "stats": {
            "str": player.str_stat,
            "agi": player.agi,
            "vit": player.vit,
            "int": player.int_stat,
            "wil": player.wil,
        },
    }


def quest_data(quest: QuestDefinition) -> dict:
    return {
        "definition_id": quest.id,
        "version": quest.version,
        "title": quest.title,
        "category": quest.category,
        "difficulty": quest.difficulty,
        "primary_stat": quest.primary_stat,
        "objective": quest.objective,
        "verification_policy": quest.verification_policy,
        "reward_profile": quest.reward_profile,
        "active": quest.active,
    }


def player_quest_data(player_quest: PlayerQuest) -> dict:
    return {
        "id": player_quest.id,
        "definition_id": player_quest.quest_definition_id,
        "definition_version": player_quest.quest_definition_version,
        "status": player_quest.status,
        "accepted_at": player_quest.accepted_at.isoformat(),
    }


async def idempotency_record(session: AsyncSession, player_id: str, scope: str, key: str) -> IdempotencyRecord | None:
    return await session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.actor_id == player_id,
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.key == key,
        )
    )


def require_key(key: str | None) -> str:
    if key is None or len(key) < 8 or len(key) > 128:
        raise HTTPException(status_code=400, detail="Valid Idempotency-Key is required")
    return key


def record_audit(
    session: AsyncSession,
    event_type: str,
    player_id: str | None,
    payload: dict,
    *,
    causation_id: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """Queue an auditable domain event in the same transaction as its mutation."""
    session.add(
        AuditEvent(
            event_type=event_type,
            player_id=player_id,
            payload=payload,
            causation_id=causation_id,
            correlation_id=correlation_id,
        )
    )


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "service": "the-system-awakening-api", "version": "0.1.0", "database": "ok"}


@router.post("/auth/demo", status_code=201)
async def demo_login(
    body: DemoLogin,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not settings.demo_mode:
        raise HTTPException(status_code=404, detail="Not found")
    provider_id = f"demo:{body.handle.lower()}"
    user = await session.scalar(select(User).where(User.auth_provider_id == provider_id))
    if user is None:
        user = User(auth_provider_id=provider_id)
        session.add(user)
        await session.flush()
        player = PlayerProfile(user_id=user.id, display_name=body.handle)
        session.add(player)
    else:
        player = await session.scalar(select(PlayerProfile).where(PlayerProfile.user_id == user.id))
    # Demo keeps the legacy bearer response for CLI compatibility, but the
    # browser receives the same HttpOnly session boundary as real auth.
    from .auth_routes import _create_session, _set_cookies

    session_token, csrf_token = await _create_session(session, user.id)
    await session.commit()
    _set_cookies(response, session_token, csrf_token)
    return envelope(
        {"access_token": create_access_token(user.id), "token_type": "bearer", "player": player_data(player)}
    )


@router.get("/player")
async def get_player(player: PlayerProfile = Depends(current_player)) -> dict:
    return envelope(player_data(player))


@router.get("/player/history")
async def get_player_history(
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    rows = await session.execute(
        select(PlayerQuest, RewardGrant, QuestDefinition)
        .join(RewardGrant, RewardGrant.player_quest_id == PlayerQuest.id)
        .join(QuestDefinition, QuestDefinition.id == PlayerQuest.quest_definition_id)
        .where(PlayerQuest.player_id == player.id, PlayerQuest.status == "COMPLETED")
        .order_by(PlayerQuest.completed_at.desc())
        .limit(50)
    )
    history = []
    for quest, reward, definition in rows:
        snapshot = quest.definition_snapshot or {}
        history.append(
            {
                "quest_id": quest.quest_definition_id,
                "title": definition.title,
                "difficulty": snapshot.get("difficulty", ""),
                "primary_stat": snapshot.get("primary_stat", ""),
                "exp_granted": reward.exp_granted,
                "stat_changes": reward.stat_changes,
                "completed_at": quest.completed_at.isoformat() if quest.completed_at else None,
            }
        )
    return envelope({"history": history, "total": len(history)})


@router.get("/quests/daily")
async def get_daily_board(
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Deterministic daily rotation (§97): main/side/optional per UTC date."""
    ids = (
        await session.scalars(
            select(QuestDefinition.id).where(QuestDefinition.active).order_by(QuestDefinition.id)
        )
    ).all()
    if not ids:
        return envelope({"date": date.today().isoformat(), "main": None, "side": None, "optional": []})
    day = game_today().timetuple().tm_yday
    rotation = [ids[(day + offset) % len(ids)] for offset in range(2)]
    optional = [qid for qid in ids if qid not in rotation]
    return envelope(
        {
            "date": game_today().isoformat(),
            "main": rotation[0],
            "side": rotation[1] if len(ids) > 1 else None,
            "optional": optional,
        }
    )


@router.patch("/player")
async def update_player(
    body: ProfileUpdate,
    response: Response,
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if body.display_name is not None:
        player.display_name = body.display_name
        await session.commit()
        response.status_code = 200
    return envelope(player_data(player))


@router.get("/quests")
async def list_quests(
    _: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    quests = (
        await session.scalars(
            select(QuestDefinition).where(QuestDefinition.active.is_(True)).order_by(QuestDefinition.id)
        )
    ).all()
    return envelope([quest_data(quest) for quest in quests])


@router.get("/quests/active")
async def active_quest(
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Restore the current quest/submission after a browser reload."""

    accepted = await session.scalar(
        select(PlayerQuest)
        .where(
            PlayerQuest.player_id == player.id,
            PlayerQuest.status.in_({"ACCEPTED", "SUBMITTED", "NEED_MORE_EVIDENCE", "REVIEW"}),
        )
        .order_by(PlayerQuest.accepted_at.desc())
    )
    if accepted is None:
        return envelope(None)
    submission = await session.scalar(
        select(Submission)
        .where(Submission.player_quest_id == accepted.id)
        .order_by(Submission.created_at.desc())
    )
    return envelope(
        {
            "accepted": {**player_quest_data(accepted), "definition_snapshot": accepted.definition_snapshot},
            "submission": None if submission is None else await submission_detail(session, submission),
        }
    )


@router.post("/quests/{quest_id}/accept", status_code=201)
async def accept_quest(
    quest_id: str,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    key = require_key(idempotency_key)
    player_id = player.id
    digest = request_hash({"quest_id": quest_id})
    existing = await idempotency_record(session, player_id, "quest_accept", key)
    if existing:
        if existing.request_hash != digest:
            raise HTTPException(status_code=409, detail="Idempotency key payload conflict")
        accepted = await session.get(PlayerQuest, existing.resource_id)
        response.status_code = 200
        return envelope(player_quest_data(accepted))
    quest = await session.get(QuestDefinition, quest_id)
    if quest is None or not quest.active:
        raise HTTPException(status_code=404, detail="Quest not found")
    # Parallel actives of DIFFERENT definitions are allowed (daily board §97);
    # the same definition may only be active once.
    active = await session.scalar(
        select(PlayerQuest.id).where(
            PlayerQuest.player_id == player_id,
            PlayerQuest.quest_definition_id == quest.id,
            PlayerQuest.status.in_(("ACCEPTED", "SUBMITTED", "NEED_MORE_EVIDENCE", "REVIEW")),
        )
    )
    if active is not None:
        raise HTTPException(status_code=409, detail="Quest is already active")
    completed_today = await session.scalar(
        select(PlayerQuest.id).where(
            PlayerQuest.player_id == player_id,
            PlayerQuest.quest_definition_id == quest.id,
            PlayerQuest.status == "COMPLETED",
            func.date(PlayerQuest.completed_at) == game_today(),
        )
    )
    if completed_today is not None:
        raise HTTPException(status_code=409, detail="Quest already completed today — come back tomorrow")
    accepted = PlayerQuest(
        player_id=player_id,
        quest_definition_id=quest.id,
        quest_definition_version=quest.version,
        definition_snapshot=quest_snapshot(quest),
    )
    session.add(accepted)
    try:
        await session.flush()
        session.add(
            IdempotencyRecord(
                actor_id=player_id,
                scope="quest_accept",
                key=key,
                request_hash=digest,
                resource_id=accepted.id,
            )
        )
        record_audit(
            session,
            "quest.accepted",
            player_id,
            {"quest_id": quest.id, "player_quest_id": accepted.id},
            causation_id=accepted.id,
        )
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        winner = await idempotency_record(session, player_id, "quest_accept", key)
        if winner is not None and winner.request_hash == digest:
            accepted = await session.get(PlayerQuest, winner.resource_id)
            response.status_code = 200
        else:
            raise HTTPException(status_code=409, detail="Quest is already active") from error
    return envelope(player_quest_data(accepted))


@router.post("/quests/{player_quest_id}/submissions", status_code=202)
async def create_submission(
    player_quest_id: str,
    body: SubmissionRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    key = require_key(idempotency_key)
    player_id = player.id
    evidence = body.manual_evidence.model_dump(exclude_none=True)
    digest = request_hash({"evidence_type": body.evidence_type, "manual_evidence": evidence})
    existing = await idempotency_record(session, player_id, "submission", key)
    if existing:
        if existing.request_hash != digest:
            raise HTTPException(status_code=409, detail="Idempotency key payload conflict")
        submission = await session.get(Submission, existing.resource_id)
        if submission is None or submission.player_quest_id != player_quest_id:
            raise HTTPException(status_code=409, detail="Idempotency key resource conflict")
        return envelope(
            {"id": submission.id, "player_quest_id": submission.player_quest_id, "status": submission.status}
        )
    accepted = await session.scalar(
        select(PlayerQuest)
        .where(PlayerQuest.id == player_quest_id, PlayerQuest.player_id == player_id)
        .with_for_update()
    )
    if accepted is None:
        raise HTTPException(status_code=404, detail="Accepted quest not found")
    if accepted.status not in {"ACCEPTED", "NEED_MORE_EVIDENCE"}:
        raise HTTPException(status_code=409, detail="Quest cannot accept evidence in its current state")
    submission = Submission(
        player_quest_id=accepted.id,
        player_id=player_id,
        idempotency_key=key,
        request_hash=digest,
        evidence_type=body.evidence_type,
        manual_evidence=evidence,
    )
    accepted.status = "SUBMITTED"
    session.add(submission)
    try:
        await session.flush()
        session.add(
            IdempotencyRecord(
                actor_id=player_id,
                scope="submission",
                key=key,
                request_hash=digest,
                resource_id=submission.id,
            )
        )
        record_audit(
            session,
            "submission.created",
            player_id,
            {"submission_id": submission.id, "player_quest_id": accepted.id},
            causation_id=submission.id,
        )
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        winner = await idempotency_record(session, player_id, "submission", key)
        if winner is None or winner.request_hash != digest:
            raise HTTPException(status_code=409, detail="Concurrent idempotency conflict") from error
        submission = await session.get(Submission, winner.resource_id)
    return envelope({"id": submission.id, "player_quest_id": player_quest_id, "status": submission.status})


@router.post("/submissions/{submission_id}/finalize", status_code=202)
async def finalize_submission(
    submission_id: str,
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Close evidence collection and make the submission worker-visible."""

    submission = await session.scalar(
        select(Submission)
        .where(Submission.id == submission_id, Submission.player_id == player.id)
        .with_for_update()
    )
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.status == "CREATED":
        submission.status = "SUBMITTED"
        record_audit(
            session,
            "submission.finalized",
            player.id,
            {"submission_id": submission.id, "player_quest_id": submission.player_quest_id},
            causation_id=submission.id,
        )
        await session.commit()
    elif submission.status not in {"SUBMITTED", "DECIDED"}:
        raise HTTPException(status_code=409, detail="Submission cannot be finalized in its current state")
    return envelope({"id": submission.id, "player_quest_id": submission.player_quest_id, "status": submission.status})


async def submission_detail(session: AsyncSession, submission: Submission) -> dict:
    verification = await session.scalar(
        select(VerificationResult).where(VerificationResult.submission_id == submission.id)
    )
    reward = await session.scalar(select(RewardGrant).where(RewardGrant.submission_id == submission.id))
    chest = None
    if reward:
        chest = await session.scalar(select(Chest).where(Chest.reward_grant_id == reward.id))
    return {
        "id": submission.id,
        "player_quest_id": submission.player_quest_id,
        "status": submission.status,
        "verification": None
        if verification is None
        else {
            "decision": verification.decision,
            "reason_code": verification.reason_code,
            "extracted_facts": verification.extracted_facts,
            "schema_version": verification.schema_version,
            "fallback_used": verification.fallback_used,
        },
        "reward": None
        if reward is None
        else {
            "id": reward.id,
            "exp_granted": reward.exp_granted,
            "stat_changes": reward.stat_changes,
            "rules_version": reward.rules_version,
            "chest_id": chest.id,
        },
    }


@router.get("/submissions/{submission_id}")
async def get_submission(
    submission_id: str,
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    submission = await session.scalar(
        select(Submission).where(Submission.id == submission_id, Submission.player_id == player.id)
    )
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return envelope(await submission_detail(session, submission))


def observation_for(quest: QuestRules, evidence: dict) -> tuple[str, dict, str]:
    objective_type = quest.objective.get("type")
    target = quest.objective.get("target")
    observed = evidence.get(objective_type)
    facts = {objective_type: observed}
    if observed is None:
        return "NEED_MORE_EVIDENCE", facts, "required_observation_missing"
    if not settings.demo_mode and not evidence.get("image_asset"):
        # Contract (06_API_SPEC + 10_TEST_PLAN "low-quality evidence → resubmit
        # state"): manual evidence without the required artifact goes back to
        # the player for resubmission instead of a terminal REVIEW.
        return "NEED_MORE_EVIDENCE", facts, "manual_evidence_requires_image"
    if objective_type == "completion" and isinstance(observed, bool):
        return ("PASS", facts, "criteria_met") if observed else ("FAIL", facts, "criteria_not_met")
    if isinstance(target, (int, float)) and isinstance(observed, (int, float)) and not isinstance(observed, bool):
        return ("PASS", facts, "criteria_met") if observed >= target else ("FAIL", facts, "criteria_not_met")
    return "REVIEW", facts, "observation_type_mismatch"


async def settle_verified_submission(
    session: AsyncSession,
    player: PlayerProfile,
    submission: Submission,
    accepted: PlayerQuest,
    quest: QuestRules,
) -> list[dict]:
    existing = await session.scalar(
        select(RewardGrant).where(RewardGrant.player_quest_id == accepted.id)
    )
    if existing:
        return []
    exp, stat_gain = calculate_quest_reward(
        quest.difficulty, "PASS", player.streak_days, quest.rules_version
    )
    stat_attribute = {"STR": "str_stat", "AGI": "agi", "VIT": "vit", "INT": "int_stat", "WIL": "wil"}[
        quest.primary_stat
    ]
    stat_changes = {quest.primary_stat: stat_gain} if stat_gain else {}
    player.current_xp += exp
    player.level = level_from_exp(player.current_xp)
    if stat_gain:
        setattr(player, stat_attribute, getattr(player, stat_attribute) + stat_gain)
    reward = RewardGrant(
        player_id=player.id,
        player_quest_id=accepted.id,
        submission_id=submission.id,
        exp_granted=exp,
        stat_changes=stat_changes,
    )
    session.add(reward)
    await session.flush()
    session.add(
        ProgressionLedger(player_id=player.id, reward_grant_id=reward.id, entry_type="EXP", stat_name=None, amount=exp)
    )
    if stat_gain:
        session.add(
            ProgressionLedger(
                player_id=player.id,
                reward_grant_id=reward.id,
                entry_type="STAT",
                stat_name=quest.primary_stat,
                amount=stat_gain,
            )
        )
    session.add(Chest(player_id=player.id, reward_grant_id=reward.id))
    record_audit(
        session,
        "reward.granted",
        player.id,
        {"reward_id": reward.id, "submission_id": submission.id, "exp": exp, "stat_changes": stat_changes},
        causation_id=submission.id,
    )
    accepted.status = "COMPLETED"
    accepted.completed_at = datetime.now(UTC)
    update_daily_streak(player, game_today())
    return await evaluate_achievements(session, player)


GAME_TZ = timezone(timedelta(hours=7))


def game_today() -> date:
    """The game day for the Thai audience — fixed UTC+7, no DST drift."""
    return datetime.now(GAME_TZ).date()


def update_daily_streak(player: PlayerProfile, today: date) -> None:
    """Daily streak: same day keeps the streak, yesterday extends it, a gap resets to 1.

    Deterministic per Game Rules; multi-quest days never inflate the counter.
    """
    last = player.last_quest_date
    if last == today:
        return
    if last == today - timedelta(days=1):
        player.streak_days += 1
    else:
        player.streak_days = 1
    player.last_quest_date = today


@router.post("/submissions/{submission_id}/verify")
async def verify_submission(
    submission_id: str,
    verification_token: str | None = Header(default=None, alias="X-Verification-Token"),
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    # Production settlement is performed only by the authenticated internal
    # worker; the browser-facing verification endpoint is demo/staging only.
    if settings.app_env == "production":
        raise HTTPException(status_code=404, detail="Submission not found")
    if not settings.demo_mode and (
        verification_token is None
        or not secrets.compare_digest(verification_token, settings.verification_token)
    ):
        raise HTTPException(status_code=404, detail="Submission not found")
    candidate = await session.scalar(
        select(Submission).where(Submission.id == submission_id, Submission.player_id == player.id)
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    locked_player = await session.scalar(
        select(PlayerProfile)
        .where(PlayerProfile.id == player.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    accepted = await session.scalar(
        select(PlayerQuest)
        .where(PlayerQuest.id == candidate.player_quest_id, PlayerQuest.player_id == player.id)
        .with_for_update()
    )
    submission = await session.scalar(
        select(Submission)
        .where(Submission.id == submission_id, Submission.player_id == player.id)
        .with_for_update()
    )
    if locked_player is None or accepted is None or submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    existing = await session.scalar(select(VerificationResult).where(VerificationResult.submission_id == submission.id))
    if existing:
        return envelope(await submission_detail(session, submission))
    quest = accepted_rules(accepted)
    decision, facts, reason = observation_for(quest, submission.manual_evidence or {})
    session.add(
        VerificationResult(
            submission_id=submission.id,
            decision=decision,
            extracted_facts=facts,
            reason_code=reason,
            fallback_used=settings.demo_mode,
        )
    )
    record_audit(
        session,
        "submission.verified",
        locked_player.id,
        {"submission_id": submission.id, "decision": decision, "reason_code": reason},
        causation_id=submission.id,
    )
    submission.status = "DECIDED"
    unlocked: list[dict] = []
    if decision == "PASS":
        unlocked = await settle_verified_submission(session, locked_player, submission, accepted, quest)
    elif decision == "NEED_MORE_EVIDENCE":
        accepted.status = "NEED_MORE_EVIDENCE"
    else:
        accepted.status = decision
    await session.commit()
    detail = await submission_detail(session, submission)
    if unlocked:
        detail["achievements_unlocked"] = unlocked
    return envelope(detail)


async def opened_data(session: AsyncSession, chest: Chest, result: ChestOpenResult) -> dict:
    item = await session.get(InventoryItem, result.item_instance_id)
    definition = await session.get(ItemDefinition, item.item_definition_id)
    return {
        "chest_id": chest.id,
        "rarity": chest.rarity,
        "item": {
            "id": item.id,
            "definition_id": definition.id,
            "name": definition.name,
            "rarity": definition.rarity,
            "power": definition.power,
        },
    }


@router.post("/chests/{chest_id}/open", status_code=201)
async def open_chest(
    chest_id: str,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    key = require_key(idempotency_key)
    player_id = player.id
    chest = await session.scalar(
        select(Chest).where(Chest.id == chest_id, Chest.player_id == player_id).with_for_update()
    )
    if chest is None:
        raise HTTPException(status_code=404, detail="Chest not found")
    digest = request_hash({"chest_id": chest_id})
    key_record = await idempotency_record(session, player_id, "chest_open", key)
    if key_record and key_record.request_hash != digest:
        raise HTTPException(status_code=409, detail="Idempotency key payload conflict")
    opened = await session.scalar(select(ChestOpenResult).where(ChestOpenResult.chest_id == chest.id))
    if opened:
        if key_record is not None and key_record.resource_id != opened.id:
            raise HTTPException(status_code=409, detail="Idempotency key resource conflict")
        if key_record is None:
            session.add(
                IdempotencyRecord(
                    actor_id=player_id,
                    scope="chest_open",
                    key=key,
                    request_hash=digest,
                    resource_id=opened.id,
                )
            )
            await session.commit()
        response.status_code = 200
        replayed = await opened_data(session, chest, opened)
        replayed["achievements_unlocked"] = await evaluate_achievements(session, player, commit=True)
        return envelope(replayed)
    roll = 0.0 if settings.demo_mode else secrets.randbelow(1_000_000) / 1_000_000
    rarity = chest_rarity_from_roll(roll)
    definition = await session.scalar(
        select(ItemDefinition).where(ItemDefinition.rarity == rarity).order_by(ItemDefinition.id)
    )
    if definition is None:
        raise HTTPException(status_code=409, detail="Loot table has no item for persisted rarity")
    item = InventoryItem(
        player_id=player_id,
        item_definition_id=definition.id,
        item_definition_version=definition.version,
        source_chest_id=chest.id,
    )
    session.add(item)
    await session.flush()
    opened = ChestOpenResult(
        chest_id=chest.id,
        item_instance_id=item.id,
        rng_metadata={"rng_version": "demo-fixed-v1" if settings.demo_mode else "secure-v1", "roll": roll},
    )
    session.add(opened)
    await session.flush()
    chest.rarity = rarity
    chest.status = "OPENED"
    chest.opened_at = datetime.now(UTC)
    if key_record is None:
        session.add(
            IdempotencyRecord(
                actor_id=player_id, scope="chest_open", key=key, request_hash=digest, resource_id=opened.id
            )
        )
    record_audit(
        session,
        "chest.opened",
        player_id,
        {"chest_id": chest.id, "item_instance_id": item.id, "rarity": rarity},
        causation_id=chest.id,
    )
    await session.commit()
    opened = await opened_data(session, chest, opened)
    opened["achievements_unlocked"] = await evaluate_achievements(session, player, commit=True)
    return envelope(opened)


@router.get("/inventory")
async def get_inventory(
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    items = (
        await session.scalars(
            select(InventoryItem).where(InventoryItem.player_id == player.id).order_by(InventoryItem.created_at)
        )
    ).all()
    data = []
    for item in items:
        definition = await session.get(ItemDefinition, item.item_definition_id)
        data.append(
            {
                "id": item.id,
                "definition_id": definition.id,
                "name": definition.name,
                "rarity": definition.rarity,
                "power": definition.power,
            }
        )
    return envelope(data)

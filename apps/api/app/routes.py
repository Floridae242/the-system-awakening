import hashlib
import json
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import create_access_token, current_player
from .config import settings
from .database import get_session
from .game_engine import calculate_quest_reward, chest_rarity_from_roll, level_from_exp
from .models import (
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


class SubmissionRequest(BaseModel):
    evidence_type: str = Field(pattern=r"^manual$")
    manual_evidence: dict = Field(default_factory=dict)


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


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "service": "the-system-awakening-api", "version": "0.1.0", "database": "ok"}


@router.post("/auth/demo", status_code=201)
async def demo_login(body: DemoLogin, session: AsyncSession = Depends(get_session)) -> dict:
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
    await session.commit()
    return envelope(
        {"access_token": create_access_token(user.id), "token_type": "bearer", "player": player_data(player)}
    )


@router.get("/player")
async def get_player(player: PlayerProfile = Depends(current_player)) -> dict:
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


@router.post("/quests/{quest_id}/accept", status_code=201)
async def accept_quest(
    quest_id: str,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    key = require_key(idempotency_key)
    digest = request_hash({"quest_id": quest_id})
    existing = await idempotency_record(session, player.id, "quest_accept", key)
    if existing:
        if existing.request_hash != digest:
            raise HTTPException(status_code=409, detail="Idempotency key payload conflict")
        accepted = await session.get(PlayerQuest, existing.resource_id)
        response.status_code = 200
        return envelope(player_quest_data(accepted))
    quest = await session.get(QuestDefinition, quest_id)
    if quest is None or not quest.active:
        raise HTTPException(status_code=404, detail="Quest not found")
    accepted = PlayerQuest(
        player_id=player.id,
        quest_definition_id=quest.id,
        quest_definition_version=quest.version,
    )
    session.add(accepted)
    await session.flush()
    session.add(
        IdempotencyRecord(
            actor_id=player.id, scope="quest_accept", key=key, request_hash=digest, resource_id=accepted.id
        )
    )
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        winner = await idempotency_record(session, player.id, "quest_accept", key)
        if winner is None or winner.request_hash != digest:
            raise HTTPException(status_code=409, detail="Concurrent idempotency conflict") from error
        accepted = await session.get(PlayerQuest, winner.resource_id)
        response.status_code = 200
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
    accepted = await session.scalar(
        select(PlayerQuest).where(PlayerQuest.id == player_quest_id, PlayerQuest.player_id == player.id)
    )
    if accepted is None:
        raise HTTPException(status_code=404, detail="Accepted quest not found")
    if accepted.status not in {"ACCEPTED", "NEED_MORE_EVIDENCE"}:
        raise HTTPException(status_code=409, detail="Quest cannot accept evidence in its current state")
    digest = request_hash(body.model_dump())
    existing = await idempotency_record(session, player.id, "submission", key)
    if existing:
        if existing.request_hash != digest:
            raise HTTPException(status_code=409, detail="Idempotency key payload conflict")
        return envelope({"id": existing.resource_id, "player_quest_id": accepted.id, "status": "CREATED"})
    submission = Submission(
        player_quest_id=accepted.id,
        player_id=player.id,
        idempotency_key=key,
        request_hash=digest,
        evidence_type=body.evidence_type,
        manual_evidence=body.manual_evidence,
    )
    accepted.status = "SUBMITTED"
    session.add(submission)
    await session.flush()
    session.add(
        IdempotencyRecord(
            actor_id=player.id, scope="submission", key=key, request_hash=digest, resource_id=submission.id
        )
    )
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        winner = await idempotency_record(session, player.id, "submission", key)
        if winner is None or winner.request_hash != digest:
            raise HTTPException(status_code=409, detail="Concurrent idempotency conflict") from error
        submission = await session.get(Submission, winner.resource_id)
    return envelope({"id": submission.id, "player_quest_id": player_quest_id, "status": submission.status})


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


def observation_for(quest: QuestDefinition, evidence: dict) -> tuple[str, dict, str]:
    objective_type = quest.objective.get("type")
    target = quest.objective.get("target")
    observed = evidence.get(objective_type)
    facts = {objective_type: observed}
    if observed is None:
        return "NEED_MORE_EVIDENCE", facts, "required_observation_missing"
    if not settings.demo_mode:
        return "REVIEW", facts, "manual_evidence_requires_review"
    if isinstance(target, (int, float)) and isinstance(observed, (int, float)) and not isinstance(observed, bool):
        return ("PASS", facts, "criteria_met") if observed >= target else ("FAIL", facts, "criteria_not_met")
    return "REVIEW", facts, "observation_type_mismatch"


async def settle_verified_submission(
    session: AsyncSession,
    player: PlayerProfile,
    submission: Submission,
    accepted: PlayerQuest,
    quest: QuestDefinition,
) -> None:
    existing = await session.scalar(select(RewardGrant).where(RewardGrant.submission_id == submission.id))
    if existing:
        return
    exp, stat_gain = calculate_quest_reward(quest.difficulty, "PASS", player.streak_days)
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
    accepted.status = "COMPLETED"
    accepted.completed_at = datetime.now(UTC)


@router.post("/submissions/{submission_id}/verify")
async def verify_submission(
    submission_id: str,
    verification_token: str | None = Header(default=None, alias="X-Verification-Token"),
    player: PlayerProfile = Depends(current_player),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not settings.demo_mode and (
        verification_token is None
        or not secrets.compare_digest(verification_token, settings.verification_token)
    ):
        raise HTTPException(status_code=404, detail="Submission not found")
    submission = await session.scalar(
        select(Submission)
        .where(Submission.id == submission_id, Submission.player_id == player.id)
        .with_for_update()
    )
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    existing = await session.scalar(select(VerificationResult).where(VerificationResult.submission_id == submission.id))
    if existing:
        return envelope(await submission_detail(session, submission))
    accepted = await session.scalar(
        select(PlayerQuest).where(PlayerQuest.id == submission.player_quest_id, PlayerQuest.player_id == player.id)
    )
    quest = await session.get(QuestDefinition, accepted.quest_definition_id)
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
    submission.status = "DECIDED"
    if decision == "PASS":
        await settle_verified_submission(session, player, submission, accepted, quest)
    elif decision == "NEED_MORE_EVIDENCE":
        accepted.status = "NEED_MORE_EVIDENCE"
    else:
        accepted.status = decision
    await session.commit()
    return envelope(await submission_detail(session, submission))


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
    chest = await session.scalar(
        select(Chest).where(Chest.id == chest_id, Chest.player_id == player.id).with_for_update()
    )
    if chest is None:
        raise HTTPException(status_code=404, detail="Chest not found")
    digest = request_hash({"chest_id": chest_id})
    key_record = await idempotency_record(session, player.id, "chest_open", key)
    if key_record and key_record.request_hash != digest:
        raise HTTPException(status_code=409, detail="Idempotency key payload conflict")
    opened = await session.scalar(select(ChestOpenResult).where(ChestOpenResult.chest_id == chest.id))
    if opened:
        response.status_code = 200
        return envelope(await opened_data(session, chest, opened))
    roll = 0.0 if settings.demo_mode else secrets.randbelow(1_000_000) / 1_000_000
    rarity = chest_rarity_from_roll(roll)
    definition = await session.scalar(
        select(ItemDefinition).where(ItemDefinition.rarity == rarity).order_by(ItemDefinition.id)
    )
    if definition is None:
        raise HTTPException(status_code=409, detail="Loot table has no item for persisted rarity")
    item = InventoryItem(
        player_id=player.id,
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
                actor_id=player.id, scope="chest_open", key=key, request_hash=digest, resource_id=opened.id
            )
        )
    await session.commit()
    return envelope(await opened_data(session, chest, opened))


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

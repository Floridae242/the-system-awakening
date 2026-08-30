"""Internal verification worker boundary.

The browser-facing API must not be trusted to decide verification.  This
module provides the small, authenticated worker boundary used by a queue
consumer (or an internal HTTP call) and reuses the same deterministic policy
and settlement code as the demo flow.
"""

import asyncio
import secrets
from dataclasses import dataclass

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_session
from .models import PlayerProfile, PlayerQuest, Submission, VerificationResult

router = APIRouter(prefix="/api/v1/internal", tags=["internal-verification"])


def require_worker_token(token: str | None) -> None:
    """Reject every request without the private worker credential.

    A missing configured token is deliberately fail-closed, including in
    development.  This endpoint is never exposed as a browser auth path.
    """

    configured = settings.verification_token
    if not token or not configured or not secrets.compare_digest(token, configured):
        raise HTTPException(status_code=404, detail="Not found")


@dataclass(frozen=True)
class VerificationWorker:
    """Single-submission worker with bounded execution and safe retries."""

    timeout_seconds: float = 30.0

    async def process(self, session: AsyncSession, submission_id: str) -> dict:
        """Verify and settle one submission.

        The submission row is locked before reading its result.  Therefore a
        retry, or two workers receiving the same job, observes the persisted
        result and cannot create another reward.  The surrounding transaction
        is committed only after verification and settlement both succeed.
        """

        # Imported lazily so the core routes may optionally delegate their
        # production path to this worker without creating an import cycle.
        from .routes import accepted_rules, observation_for, record_audit, settle_verified_submission, submission_detail

        async with session.begin():
            candidate = await session.scalar(select(Submission).where(Submission.id == submission_id))
            if candidate is None:
                raise HTTPException(status_code=404, detail="Submission not found")
            # Keep the same lock order as the browser-facing path to prevent
            # cross-worker deadlocks when both receive the same submission.
            player = await session.scalar(
                select(PlayerProfile)
                .where(PlayerProfile.id == candidate.player_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            accepted = await session.scalar(
                select(PlayerQuest).where(PlayerQuest.id == candidate.player_quest_id).with_for_update()
            )
            submission = await session.scalar(
                select(Submission).where(Submission.id == submission_id).with_for_update()
            )
            if submission is None:
                raise HTTPException(status_code=404, detail="Submission not found")
            existing = await session.scalar(
                select(VerificationResult).where(VerificationResult.submission_id == submission.id)
            )
            if existing is not None:
                return await submission_detail(session, submission)
            if accepted is None or player is None or accepted.player_id != player.id:
                raise HTTPException(status_code=404, detail="Submission not found")

            quest = accepted_rules(accepted)
            decision, facts, reason = observation_for(quest, submission.manual_evidence or {})
            session.add(
                VerificationResult(
                    submission_id=submission.id,
                    decision=decision,
                    extracted_facts=facts,
                    reason_code=reason,
                    fallback_used=True,
                )
            )
            record_audit(
                session,
                "submission.verified",
                player.id,
                {"submission_id": submission.id, "decision": decision, "reason_code": reason},
                causation_id=submission.id,
            )
            submission.status = "DECIDED"
            if decision == "PASS":
                await settle_verified_submission(session, player, submission, accepted, quest)
            elif decision == "NEED_MORE_EVIDENCE":
                accepted.status = "NEED_MORE_EVIDENCE"
            else:
                accepted.status = decision

        return await submission_detail(session, submission)

    async def process_with_timeout(self, session: AsyncSession, submission_id: str) -> dict:
        """Queue-consumer entry point; cancellation rolls back the transaction."""

        return await asyncio.wait_for(self.process(session, submission_id), timeout=self.timeout_seconds)


worker = VerificationWorker()


@router.post("/submissions/{submission_id}/verify")
async def verify_internal_submission(
    submission_id: str,
    verification_token: str | None = Header(default=None, alias="X-Verification-Token"),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict:
    """Authenticated worker-only verification endpoint.

    No ``current_player`` dependency is intentionally present: jobs are
    authorized by the service credential and ownership is derived from the
    locked database rows, never from caller-supplied player identity.
    """

    require_worker_token(verification_token)
    return {"success": True, "data": await worker.process_with_timeout(session, submission_id)}

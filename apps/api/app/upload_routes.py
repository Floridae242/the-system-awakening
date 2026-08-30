"""Authenticated image evidence endpoint.

Include ``router`` from :mod:`app.application`; keeping this router separate
lets deployments omit uploads without changing the core progression routes.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from .auth import current_player
from .database import get_session
from .models import PlayerProfile, Submission
from .uploads import read_validated_image, remove_private_image, store_private_image

router = APIRouter(prefix="/api/v1")


@router.post("/submissions/{submission_id}/evidence/image", status_code=201)
async def upload_image_evidence(
    submission_id: str,
    image: UploadFile = File(...),  # noqa: B008
    player: PlayerProfile = Depends(current_player),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict:
    submission = await session.scalar(
        select(Submission).where(Submission.id == submission_id, Submission.player_id == player.id)
    )
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.status not in {"CREATED", "SUBMITTED", "NEED_MORE_EVIDENCE", "REVIEW"}:
        raise HTTPException(status_code=409, detail="Submission cannot accept evidence in its current state")
    validated = await read_validated_image(image)
    metadata = store_private_image(validated, owner_id=player.id, submission_id=submission.id)
    evidence = dict(submission.manual_evidence or {})
    evidence["image_asset"] = {key: value for key, value in metadata.items() if key != "owner_id"}
    submission.manual_evidence = evidence
    flag_modified(submission, "manual_evidence")
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        remove_private_image(metadata)
        raise
    return {"success": True, "data": {key: value for key, value in metadata.items() if key != "owner_id"}}

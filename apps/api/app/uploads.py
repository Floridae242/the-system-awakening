"""Private, content-validated evidence image storage.

This module deliberately has no public static-file handler.  Callers receive
metadata only; the generated object key is an internal storage reference.
"""

from __future__ import annotations

import hashlib
import io
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
_PNG = b"\x89PNG\r\n\x1a\n"
_JPEG = b"\xff\xd8\xff"
_WEBP_RIFF = b"RIFF"
_WEBP_MARKER = b"WEBP"


@dataclass(frozen=True)
class ValidatedImage:
    media_type: str
    extension: str
    size_bytes: int
    sha256: str
    data: bytes


def _detect_type(data: bytes) -> tuple[str, str] | None:
    # Require the structural terminators/signature, not just a spoofed prefix.
    if data.startswith(_PNG) and len(data) >= 24 and data[12:16] == b"IHDR" and data.endswith(b"IEND\xaeB`\x82"):
        return "image/png", ".png"
    if data.startswith(_JPEG) and data.endswith(b"\xff\xd9"):
        return "image/jpeg", ".jpg"
    if (
        len(data) >= 12
        and data.startswith(_WEBP_RIFF)
        and data[8:12] == _WEBP_MARKER
        and int.from_bytes(data[4:8], "little") <= len(data) - 8
    ):
        return "image/webp", ".webp"
    return None


def validate_image_bytes(data: bytes, declared_type: str | None = None) -> ValidatedImage:
    """Validate size, magic bytes and (when supplied) declared MIME type."""
    if not data:
        raise HTTPException(status_code=400, detail="Image file is empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image file exceeds 8 MiB limit")
    detected = _detect_type(data)
    if detected is None:
        raise HTTPException(status_code=415, detail="Unsupported or invalid image format")
    media_type, extension = detected
    if declared_type and declared_type != media_type:
        raise HTTPException(status_code=415, detail="Image content type does not match its bytes")
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}[media_type]:
                raise HTTPException(status_code=415, detail="Image content type does not match its bytes")
            width, height = image.size
            if width < 1 or height < 1 or width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Image dimensions exceed the safety limit")
            image.verify()
        # verify() does not decode pixels; load a second instance to reject
        # truncated or malformed payloads that pass container checks.
        with Image.open(io.BytesIO(data)) as image:
            image.load()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise HTTPException(status_code=415, detail="Unsupported or invalid image format") from error
    return ValidatedImage(media_type, extension, len(data), hashlib.sha256(data).hexdigest(), data)


def storage_root() -> Path:
    root = Path(os.getenv("EVIDENCE_STORAGE_DIR", "/tmp/awakening-evidence")).expanduser().resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    return root


def store_private_image(image: ValidatedImage, *, owner_id: str, submission_id: str) -> dict:
    """Atomically store an already validated image and return non-public metadata."""
    root = storage_root()
    owner_dir = root / secrets.token_hex(16)
    owner_dir.mkdir(mode=0o700)
    object_name = f"{uuid4().hex}{image.extension}"
    target = owner_dir / object_name
    # The path is generated above and never derived from client input.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(image.data)
        os.chmod(target, 0o600)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return {
        "asset_id": uuid4().hex,
        "owner_id": owner_id,
        "submission_id": submission_id,
        "media_type": image.media_type,
        "size_bytes": image.size_bytes,
        "sha256": image.sha256,
        "object_key": f"{owner_dir.name}/{object_name}",
    }


def remove_private_image(metadata: dict) -> None:
    """Best-effort compensation when the metadata transaction cannot commit."""
    key = metadata.get("object_key")
    parts = key.split("/") if isinstance(key, str) else []
    if len(parts) != 2 or any(part in {"", ".", ".."} for part in parts):
        return
    target = storage_root() / key
    try:
        target.unlink(missing_ok=True)
        target.parent.rmdir()
    except OSError:
        pass


async def read_validated_image(upload: UploadFile) -> ValidatedImage:
    """Read an upload with a hard cap; client filename is intentionally ignored."""
    data = await upload.read(MAX_IMAGE_BYTES + 1)
    return validate_image_bytes(data, upload.content_type)

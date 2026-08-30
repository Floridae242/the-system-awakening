import io

import pytest
from fastapi import HTTPException
from PIL import Image

from app.uploads import MAX_IMAGE_BYTES, store_private_image, validate_image_bytes


def _image(format: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), "#29d9ff").save(buffer, format=format)
    return buffer.getvalue()


PNG = _image("PNG")
JPEG = _image("JPEG")
WEBP = _image("WEBP")


@pytest.mark.parametrize(
    ("data", "media_type", "extension"),
    [(PNG, "image/png", ".png"), (JPEG, "image/jpeg", ".jpg"), (WEBP, "image/webp", ".webp")],
)
def test_validation_uses_magic_bytes(data, media_type, extension):
    result = validate_image_bytes(data, media_type)
    assert (result.media_type, result.extension, result.size_bytes) == (media_type, extension, len(data))
    assert len(result.sha256) == 64


def test_rejects_extension_spoof_and_mime_mismatch():
    with pytest.raises(HTTPException) as invalid:
        validate_image_bytes(b"not-an-image", "image/png")
    assert invalid.value.status_code == 415
    with pytest.raises(HTTPException) as mismatch:
        validate_image_bytes(PNG, "image/jpeg")
    assert mismatch.value.status_code == 415


def test_rejects_empty_and_oversized_images():
    with pytest.raises(HTTPException) as empty:
        validate_image_bytes(b"")
    assert empty.value.status_code == 400
    with pytest.raises(HTTPException) as oversized:
        validate_image_bytes(PNG + b"x" * (MAX_IMAGE_BYTES + 1), "image/png")
    assert oversized.value.status_code == 413


def test_storage_is_private_and_filename_is_not_used(tmp_path, monkeypatch):
    monkeypatch.setenv("EVIDENCE_STORAGE_DIR", str(tmp_path / "evidence"))
    image = validate_image_bytes(PNG, "image/png")
    metadata = store_private_image(image, owner_id="player-1", submission_id="submission-1")
    root = tmp_path / "evidence"
    stored = root / metadata["object_key"]
    assert stored.read_bytes() == PNG
    assert stored.stat().st_mode & 0o777 == 0o600
    assert root.stat().st_mode & 0o777 == 0o700
    assert "../" not in metadata["object_key"]
    assert "filename" not in metadata

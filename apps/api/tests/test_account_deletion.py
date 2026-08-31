"""Privacy baseline: account deletion removes profile, activity and evidence files."""

import io
import time
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.uploads import storage_root
from main import app


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (64, 217, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def _register(client: TestClient, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 201
    return response.json()["data"]["csrf_token"]


def _storage_files() -> set[Path]:
    root = storage_root()
    if not root.exists():
        return set()
    return {path for path in root.rglob("*") if path.is_file()}


def test_delete_account_erases_profile_activity_and_evidence():
    with TestClient(app) as client:
        email = f"delete-me-{time.time()}@test.local"
        csrf = _register(client, email)
        headers = {"x-csrf-token": csrf}

        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers={**headers, "Idempotency-Key": "delete-accept"},
        ).json()["data"]
        submitted = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers={**headers, "Idempotency-Key": "delete-submit"},
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
        ).json()["data"]
        before = _storage_files()
        uploaded = client.post(
            f"/api/v1/submissions/{submitted['id']}/evidence/image",
            headers=headers,
            files={"image": ("evidence.png", _png(), "image/png")},
        )
        assert uploaded.status_code == 201
        after_upload = _storage_files()
        assert len(after_upload) == len(before) + 1

        deleted = client.delete("/api/v1/auth/account", headers=headers)
        assert deleted.status_code == 204

        assert client.get("/api/v1/auth/me").status_code == 401
        assert _storage_files() == before


def test_delete_account_requires_matching_csrf():
    with TestClient(app) as client:
        _register(client, f"csrf-check-{time.time()}@test.local")
        response = client.delete("/api/v1/auth/account", headers={"x-csrf-token": "wrong-value"})
        assert response.status_code == 403

import asyncio
import io
from dataclasses import replace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

from app import routes
from app import verification_worker as module
from main import app


def _auth_headers(client: TestClient, handle: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/demo", json={"handle": handle})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_worker_token_is_fail_closed_without_configuration():
    with pytest.raises(HTTPException) as error:
        module.require_worker_token("anything")
    assert error.value.status_code == 404


def test_worker_token_uses_constant_time_comparison(monkeypatch):
    monkeypatch.setattr(module, "settings", replace(module.settings, verification_token="x" * 32))
    module.require_worker_token("x" * 32)
    with pytest.raises(HTTPException) as error:
        module.require_worker_token("y" * 32)
    assert error.value.status_code == 404


def test_worker_timeout_is_bounded():
    class SlowWorker(module.VerificationWorker):
        async def process(self, session, submission_id):
            await asyncio.sleep(1)
            return {}

    async def run():
        with pytest.raises(asyncio.TimeoutError):
            await SlowWorker(timeout_seconds=0.001).process_with_timeout(None, "submission")

    asyncio.run(run())


def test_production_submission_is_processed_by_internal_worker(monkeypatch):
    """Production must never require the browser-only verify endpoint."""

    with TestClient(app) as client:
        headers = _auth_headers(client, "production-worker")
        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers={**headers, "Idempotency-Key": "production-worker-accept"},
        ).json()["data"]
        monkeypatch.setattr(routes, "settings", replace(routes.settings, app_env="production", demo_mode=False))

        submitted = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers={**headers, "Idempotency-Key": "production-worker-submit"},
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
        )

        assert submitted.status_code == 202
        assert asyncio.run(module.process_pending_submissions()) == 0
        restored = client.get("/api/v1/quests/active", headers=headers)
        assert restored.json()["data"]["submission"]["id"] == submitted.json()["data"]["id"]
        before_finalize = client.get(f"/api/v1/submissions/{submitted.json()['data']['id']}", headers=headers)
        assert before_finalize.json()["data"]["verification"] is None

        finalized = client.post(
            f"/api/v1/submissions/{submitted.json()['data']['id']}/finalize",
            headers=headers,
        )
        assert finalized.status_code == 202
        assert asyncio.run(module.process_pending_submissions()) == 1
        detail = client.get(f"/api/v1/submissions/{submitted.json()['data']['id']}", headers=headers)
        assert detail.status_code == 200
        body = detail.json()["data"]
        assert body["verification"]["decision"] == "NEED_MORE_EVIDENCE"
        assert body["verification"]["reason_code"] == "manual_evidence_requires_image"

        # The quest returns to a resubmittable state (06_API_SPEC / 10_TEST_PLAN
        # "low-quality evidence → resubmit state"): attaching the image unlocks it.
        png = io.BytesIO()
        Image.new("RGB", (8, 8), (64, 217, 255)).save(png, format="PNG")
        resubmitted = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers={**headers, "Idempotency-Key": "production-worker-resubmit"},
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
        )
        assert resubmitted.status_code == 202
        resubmission_id = resubmitted.json()["data"]["id"]
        uploaded = client.post(
            f"/api/v1/submissions/{resubmission_id}/evidence/image",
            headers=headers,
            files={"image": ("evidence.png", png.getvalue(), "image/png")},
        )
        assert uploaded.status_code == 201
        assert client.post(
            f"/api/v1/submissions/{resubmission_id}/finalize", headers=headers
        ).status_code == 202
        assert asyncio.run(module.process_pending_submissions()) >= 1
        settled = client.get(f"/api/v1/submissions/{resubmission_id}", headers=headers).json()["data"]
        assert settled["verification"]["decision"] == "PASS", settled["verification"]
        assert settled["reward"] is not None


def test_failed_pending_job_reports_no_progress(monkeypatch):
    """A poison job must trigger worker-loop backoff instead of a hot loop."""

    with TestClient(app) as client:
        headers = _auth_headers(client, "failed-production-worker")
        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers={**headers, "Idempotency-Key": "failed-worker-accept"},
        ).json()["data"]
        submitted = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers={**headers, "Idempotency-Key": "failed-worker-submit"},
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
        ).json()["data"]
        assert client.post(f"/api/v1/submissions/{submitted['id']}/finalize", headers=headers).status_code == 202

        async def fail(_: str) -> None:
            raise RuntimeError("synthetic worker failure")

        monkeypatch.setattr(module, "process_persisted_submission", fail)
        assert asyncio.run(module.process_pending_submissions()) == 0


def test_production_settles_image_backed_evidence(monkeypatch):
    """Image-backed manual evidence meeting criteria settles deterministically."""

    with TestClient(app) as client:
        headers = _auth_headers(client, "production-image-pass")
        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers={**headers, "Idempotency-Key": "production-image-accept"},
        ).json()["data"]
        monkeypatch.setattr(routes, "settings", replace(routes.settings, app_env="production", demo_mode=False))

        submitted = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers={**headers, "Idempotency-Key": "production-image-submit"},
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
        )
        assert submitted.status_code == 202
        submission_id = submitted.json()["data"]["id"]
        import io

        from PIL import Image

        buffer = io.BytesIO()
        Image.new("RGB", (8, 8), (64, 217, 255)).save(buffer, format="PNG")
        png = buffer.getvalue()
        uploaded = client.post(
            f"/api/v1/submissions/{submission_id}/evidence/image",
            headers=headers,
            files={"image": ("evidence.png", png, "image/png")},
        )
        assert uploaded.status_code == 201, uploaded.text
        finalized = client.post(
            f"/api/v1/submissions/{submission_id}/finalize",
            headers=headers,
        )
        assert finalized.status_code == 202
        # The scanner may also settle leftover eligible rows from earlier tests.
        assert asyncio.run(module.process_pending_submissions()) >= 1
        detail = client.get(f"/api/v1/submissions/{submission_id}", headers=headers)
        body = detail.json()["data"]
        assert body["verification"]["decision"] == "PASS", body["verification"]
        assert body["verification"]["reason_code"] == "criteria_met"
        assert body["reward"] is not None

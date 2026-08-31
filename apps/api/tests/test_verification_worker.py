import asyncio
from dataclasses import replace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

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
        assert detail.json()["data"]["verification"]["decision"] == "REVIEW"
        assert detail.json()["data"]["verification"]["reason_code"] == "manual_evidence_requires_review"


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

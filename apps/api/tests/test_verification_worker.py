import asyncio
from dataclasses import replace

import pytest
from fastapi import HTTPException

from app import verification_worker as module


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

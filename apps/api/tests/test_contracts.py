import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[3]


def test_authoritative_contracts_parse_and_use_closed_decision_enum():
    api = yaml.safe_load((ROOT / "06_API_SPEC.yaml").read_text())
    assert api["openapi"].startswith("3.1")
    decisions = api["components"]["schemas"]["VerificationResult"]["properties"]["decision"]["enum"]
    assert decisions == ["PASS", "NEED_MORE_EVIDENCE", "REVIEW", "FAIL"]
    assert "/submissions/{submission_id}/verify" in api["paths"]

    content = json.loads((ROOT / "09_CONTENT_SEED.json").read_text())
    assert content["quests"]
    assert content["items"]

import json
from pathlib import Path

import pytest

from app.game_engine import (
    calculate_quest_reward,
    chest_rarity_from_roll,
    level_from_exp,
    xp_required_for_next_level,
)

VECTORS = json.loads((Path(__file__).parents[3] / "packages/contracts/game-rules-v1.vectors.json").read_text())


def test_python_engine_matches_shared_rules_vectors():
    for vector in VECTORS["levels"]:
        assert level_from_exp(vector["total_exp"]) == vector["level"]
    assert xp_required_for_next_level(1) == 100
    assert xp_required_for_next_level(2) == 255

    for vector in VECTORS["rewards"]:
        assert calculate_quest_reward(vector["difficulty"], vector["performance"], vector["streak_days"]) == (
            vector["exp"],
            vector["stat_gain"],
        )

    for vector in VECTORS["rarity_rolls"]:
        assert chest_rarity_from_roll(vector["roll"]) == vector["rarity"]


def test_engine_rejects_invalid_authoritative_inputs():
    with pytest.raises(ValueError):
        level_from_exp(-1)
    with pytest.raises(ValueError):
        calculate_quest_reward("UNKNOWN", "PASS", 0)
    with pytest.raises(ValueError):
        chest_rarity_from_roll(1)


def test_engine_rejects_unknown_rules_version():
    with pytest.raises(ValueError, match="unsupported game rules version"):
        calculate_quest_reward("NORMAL", "PASS", 0, "9.9.9")

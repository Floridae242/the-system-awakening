import math

BASE_EXP = {"EASY": 80, "NORMAL": 120, "HARD": 180, "ELITE": 260, "EXTREME": 360}
DIFFICULTY_MULTIPLIER = {"EASY": 1.0, "NORMAL": 1.10, "HARD": 1.25, "ELITE": 1.45, "EXTREME": 1.70}
PERFORMANCE_MULTIPLIER = {"PARTIAL": 0.70, "PASS": 1.0, "STRONG": 1.10, "EXCELLENT": 1.20}


def round_half_up(value: float) -> int:
    return math.floor(value + 0.5)


def xp_required_for_next_level(level: int) -> int:
    if not isinstance(level, int) or isinstance(level, bool) or level < 1:
        raise ValueError("level must be a positive integer")
    return round_half_up(100 * level**1.35)


def level_from_exp(total_exp: int) -> int:
    if not isinstance(total_exp, int) or isinstance(total_exp, bool) or total_exp < 0:
        raise ValueError("total_exp must be a non-negative integer")
    remaining = total_exp
    level = 1
    while remaining >= xp_required_for_next_level(level):
        remaining -= xp_required_for_next_level(level)
        level += 1
    return level


def calculate_quest_reward(difficulty: str, performance: str, streak_days: int) -> tuple[int, int]:
    if difficulty not in BASE_EXP or performance not in PERFORMANCE_MULTIPLIER:
        raise ValueError("invalid difficulty or performance")
    if not isinstance(streak_days, int) or isinstance(streak_days, bool) or streak_days < 0:
        raise ValueError("streak_days must be a non-negative integer")
    consistency = 1.10 if streak_days >= 7 else 1.05 if streak_days >= 3 else 1.0
    exp = round_half_up(
        BASE_EXP[difficulty] * DIFFICULTY_MULTIPLIER[difficulty] * PERFORMANCE_MULTIPLIER[performance] * consistency
    )
    exp = min(1000, max(50, exp))
    stat_gain = (
        0
        if difficulty == "EASY"
        else 2
        if difficulty in {"HARD", "ELITE", "EXTREME"} and performance == "EXCELLENT"
        else 1
    )
    return exp, stat_gain


def chest_rarity_from_roll(roll: float) -> str:
    if not math.isfinite(roll) or roll < 0 or roll >= 1:
        raise ValueError("roll must be in [0, 1)")
    if roll < 0.55:
        return "COMMON"
    if roll < 0.75:
        return "UNCOMMON"
    if roll < 0.88:
        return "RARE"
    if roll < 0.95:
        return "EPIC"
    if roll < 0.99:
        return "LEGENDARY"
    return "MYTHIC"

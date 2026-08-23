"""Calorie calculation layer — pure functions, no I/O."""

import re

import pandas as pd

# Grams per one unit of each generic measure (Indian-kitchen approximations).
UNIT_GRAMS = {
    "gram": 1,
    "tsp": 5,
    "tbsp": 15,
    "cup": 150,
    "bowl": 200,
    "glass": 250,
    "plate": 300,
}

# Words in serving_unit that mean the food is measured by volume, not counted.
_VOLUME_WORDS = ("cup", "cups", "bowl", "glass", "plate", "tbsp", "tsp",
                 "handful", "pack")


def calories_for(calories_per_serving: float, quantity: float) -> float:
    return calories_per_serving * quantity


def _is_gram_based(serving_unit: str) -> bool:
    """True for servings stated directly in grams, e.g. '30 g' or '100 g'."""
    return bool(re.fullmatch(r"\d+(?:\.\d+)?\s*g", serving_unit.strip()))


def is_countable(serving_unit: str) -> bool:
    """True when the native serving is counted (1 roti, 6 pieces, 2 eggs …)."""
    unit = serving_unit.lower()
    if _is_gram_based(unit):
        return False
    return not any(w in unit for w in _VOLUME_WORDS)


def pieces_per_serving(serving_unit: str) -> float:
    """How many countable items one serving holds ('6 pieces' -> 6)."""
    m = re.match(r"(\d+(?:\.\d+)?)", serving_unit.strip())
    return float(m.group(1)) if m else 1.0


def unit_options(serving_unit: str) -> list[str]:
    """Units that make sense for this food, native-style unit first."""
    unit = serving_unit.lower()
    if is_countable(unit):
        return ["number", "gram"]
    if "tbsp" in unit or "tsp" in unit:
        return ["tbsp", "tsp", "gram"]
    if "small" in unit or "handful" in unit:
        return ["gram", "cup", "bowl"]
    if "glass" in unit or "ml" in unit:
        return ["glass", "cup", "bowl", "gram"]
    if "plate" in unit:
        return ["plate", "bowl", "cup", "gram"]
    if "bowl" in unit:
        return ["bowl", "cup", "gram"]
    if "cup" in unit:
        return ["cup", "bowl", "gram"]
    return ["gram", "bowl", "cup"]  # '30 g', '1 pack cooked', handful


def calories_for_unit(calories_per_serving: float, serving_weight_g: float,
                      serving_unit: str, unit: str, quantity: float) -> float:
    """Calories for `quantity` of `unit` (a UNIT_GRAMS key or 'number')."""
    if unit == "number":
        return calories_per_serving / pieces_per_serving(serving_unit) * quantity
    grams = UNIT_GRAMS[unit] * quantity
    return calories_per_serving / serving_weight_g * grams


def entries_for_date(log: pd.DataFrame, date: str) -> pd.DataFrame:
    """All log entries for one ISO date, keeping the original row index."""
    return log[log["date"] == date]


def total_for_date(log: pd.DataFrame, date: str) -> float:
    return float(entries_for_date(log, date)["calories"].sum())


def remaining(target: int, consumed: float) -> float:
    return target - consumed

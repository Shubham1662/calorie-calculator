"""CSV/JSON persistence layer.

All reads and writes for the three stores live here:
- data/foods.csv            master food database
- data/consumption_log.csv  one row per logged food entry
- data/settings.json        daily calorie target
"""

import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FOODS_CSV = DATA_DIR / "foods.csv"
LOG_CSV = DATA_DIR / "consumption_log.csv"
SETTINGS_JSON = DATA_DIR / "settings.json"

FOOD_COLUMNS = ["food_name", "category", "food_group", "serving_unit", "calories_per_serving"]
LOG_COLUMNS = ["date", "food_name", "quantity", "serving_unit", "calories"]
DEFAULT_TARGET = 2000


def load_foods() -> pd.DataFrame:
    return pd.read_csv(FOODS_CSV)


def add_food(food_name: str, category: str, food_group: str,
             serving_unit: str, calories_per_serving: float) -> bool:
    """Append a food to the database. Returns False if the name already exists."""
    foods = load_foods()
    if foods["food_name"].str.strip().str.lower().eq(food_name.strip().lower()).any():
        return False
    row = pd.DataFrame([{
        "food_name": food_name.strip(),
        "category": category,
        "food_group": food_group,
        "serving_unit": serving_unit.strip(),
        "calories_per_serving": calories_per_serving,
    }])
    pd.concat([foods, row], ignore_index=True).to_csv(FOODS_CSV, index=False)
    return True


def load_log() -> pd.DataFrame:
    if not LOG_CSV.exists():
        return pd.DataFrame(columns=LOG_COLUMNS)
    return pd.read_csv(LOG_CSV, dtype={"date": str})


def append_log_entry(date: str, food_name: str, quantity: float,
                     serving_unit: str, calories: float) -> None:
    """Add one consumption entry. `date` is an ISO string (YYYY-MM-DD)."""
    log = load_log()
    row = pd.DataFrame([{
        "date": date,
        "food_name": food_name,
        "quantity": quantity,
        "serving_unit": serving_unit,
        "calories": round(calories),
    }])
    pd.concat([log, row], ignore_index=True).to_csv(LOG_CSV, index=False)


def delete_log_entry(row_index: int) -> None:
    log = load_log()
    log.drop(index=row_index).to_csv(LOG_CSV, index=False)


def get_daily_target() -> int:
    if SETTINGS_JSON.exists():
        return int(json.loads(SETTINGS_JSON.read_text()).get("daily_target", DEFAULT_TARGET))
    return DEFAULT_TARGET


def set_daily_target(target: int) -> None:
    SETTINGS_JSON.write_text(json.dumps({"daily_target": int(target)}))

"""Persistence layer: Google Sheets in the cloud, CSV/JSON fallback locally.

When Streamlit secrets contain a [gsheets] section (service-account
credentials plus a `spreadsheet` URL), all reads and writes go to three
worksheets in that spreadsheet:
- foods            master food database
- consumption_log  one row per logged food entry
- settings         key/value pairs (daily calorie target)

Without secrets (e.g. running locally), the original file stores are used:
- data/foods.csv
- data/consumption_log.csv
- data/settings.json

On first run against an empty spreadsheet, the foods worksheet is seeded
from the bundled data/foods.csv.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FOODS_CSV = DATA_DIR / "foods.csv"
LOG_CSV = DATA_DIR / "consumption_log.csv"
SETTINGS_JSON = DATA_DIR / "settings.json"

FOOD_COLUMNS = ["food_name", "category", "food_group", "serving_unit",
                "calories_per_serving", "serving_weight_g"]
LOG_COLUMNS = ["date", "food_name", "quantity", "serving_unit", "calories"]
SETTINGS_COLUMNS = ["key", "value"]
DEFAULT_TARGET = 2000

# Sheets writes clear this cache, so the app sees its own changes instantly;
# the TTL only bounds staleness across devices/sessions.
_CACHE_TTL_S = 120


def _sheets_enabled() -> bool:
    try:
        return "gsheets" in st.secrets
    except Exception:  # no secrets.toml at all
        return False


@st.cache_resource(show_spinner=False)
def _spreadsheet():
    import gspread

    conf = dict(st.secrets["gsheets"])
    url = conf.pop("spreadsheet")
    if "refresh_token" in conf:
        # OAuth user credentials (for accounts where service-account key
        # creation is blocked). Generate with scripts/get_google_token.py.
        from google.oauth2.credentials import Credentials

        creds = Credentials(
            token=None,
            refresh_token=conf["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=conf["client_id"],
            client_secret=conf["client_secret"],
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"],
        )
        client = gspread.authorize(creds)
    else:
        client = gspread.service_account_from_dict(conf)
    return client.open_by_url(url)


def _worksheet(name: str, headers: list[str]):
    import gspread

    ss = _spreadsheet()
    try:
        return ss.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(name, rows=100, cols=len(headers))
        ws.append_row(headers, value_input_option="RAW")
        return ws


@st.cache_data(ttl=_CACHE_TTL_S, show_spinner=False)
def _read_ws(name: str, headers: tuple[str, ...]) -> pd.DataFrame:
    ws = _worksheet(name, list(headers))
    records = ws.get_all_records(expected_headers=list(headers))
    if not records:
        return pd.DataFrame(columns=list(headers))
    return pd.DataFrame(records)[list(headers)]


def _append_ws_row(name: str, headers: list[str], row: list) -> None:
    _worksheet(name, headers).append_row(row, value_input_option="RAW")
    _read_ws.clear()


# ------------------------------------------------------------------ foods

def _seed_foods_ws() -> pd.DataFrame:
    """Populate an empty foods worksheet from the bundled CSV."""
    foods = pd.read_csv(FOODS_CSV).fillna("")[FOOD_COLUMNS]
    ws = _worksheet("foods", FOOD_COLUMNS)
    ws.append_rows(foods.astype(object).values.tolist(),
                   value_input_option="RAW")
    _read_ws.clear()
    return foods


def load_foods() -> pd.DataFrame:
    if not _sheets_enabled():
        return pd.read_csv(FOODS_CSV)
    foods = _read_ws("foods", tuple(FOOD_COLUMNS))
    if foods.empty and FOODS_CSV.exists():
        foods = _seed_foods_ws()
    return foods


def add_food(food_name: str, category: str, food_group: str,
             serving_unit: str, calories_per_serving: float,
             serving_weight_g: float) -> bool:
    """Append a food to the database. Returns False if the name already exists."""
    foods = load_foods()
    if foods["food_name"].astype(str).str.strip().str.lower().eq(
            food_name.strip().lower()).any():
        return False
    values = [food_name.strip(), category, food_group, serving_unit.strip(),
              calories_per_serving, serving_weight_g]
    if _sheets_enabled():
        _append_ws_row("foods", FOOD_COLUMNS, values)
    else:
        row = pd.DataFrame([dict(zip(FOOD_COLUMNS, values))])
        pd.concat([foods, row], ignore_index=True).to_csv(FOODS_CSV, index=False)
    return True


# -------------------------------------------------------------------- log

def load_log() -> pd.DataFrame:
    if _sheets_enabled():
        log = _read_ws("consumption_log", tuple(LOG_COLUMNS))
        log["date"] = log["date"].astype(str)
        return log
    if not LOG_CSV.exists():
        return pd.DataFrame(columns=LOG_COLUMNS)
    return pd.read_csv(LOG_CSV, dtype={"date": str})


def append_log_entry(date: str, food_name: str, quantity: float,
                     serving_unit: str, calories: float) -> None:
    """Add one consumption entry. `date` is an ISO string (YYYY-MM-DD)."""
    if _sheets_enabled():
        _append_ws_row("consumption_log", LOG_COLUMNS,
                       [date, food_name, quantity, serving_unit, round(calories)])
        return
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
    if _sheets_enabled():
        # row_index is the 0-based position in the log; +2 skips the
        # 1-based sheet numbering and the header row.
        _worksheet("consumption_log", LOG_COLUMNS).delete_rows(row_index + 2)
        _read_ws.clear()
        return
    log = load_log()
    log.drop(index=row_index).to_csv(LOG_CSV, index=False)


# --------------------------------------------------------------- settings

def get_daily_target() -> int:
    if _sheets_enabled():
        settings = _read_ws("settings", tuple(SETTINGS_COLUMNS))
        match = settings.loc[settings["key"] == "daily_target", "value"]
        if not match.empty:
            return int(match.iloc[0])
        return DEFAULT_TARGET
    if SETTINGS_JSON.exists():
        return int(json.loads(SETTINGS_JSON.read_text()).get("daily_target", DEFAULT_TARGET))
    return DEFAULT_TARGET


def set_daily_target(target: int) -> None:
    if _sheets_enabled():
        ws = _worksheet("settings", SETTINGS_COLUMNS)
        ws.update(values=[SETTINGS_COLUMNS, ["daily_target", int(target)]],
                  range_name="A1:B2", raw=True)
        _read_ws.clear()
        return
    SETTINGS_JSON.write_text(json.dumps({"daily_target": int(target)}))

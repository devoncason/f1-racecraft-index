import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.config import DB_PATH, RAW_DIR, SQL_DIR, ensure_project_dirs
from src.db import get_connection, run_sql_file

PREFIX_TO_TABLE = {
    "selected_meeting_": "raw_selected_meeting",
    "selected_qualifying_session_": "raw_selected_qualifying_session",
    "selected_race_session_": "raw_selected_race_session",
    "meetings_": "raw_meetings",
    "sessions_": "raw_sessions",
    "drivers_": "raw_drivers",
    "qualifying_result_": "raw_qualifying_result",
    "starting_grid_": "raw_starting_grid",
    "race_result_": "raw_race_result",
    "laps_": "raw_laps",
    "stints_": "raw_stints",
    "pit_": "raw_pit",
    "position_": "raw_position",
    "intervals_": "raw_intervals",
    "weather_": "raw_weather",
    "race_control_": "raw_race_control",
    "overtakes_": "raw_overtakes",
}


def _table_for_file(path: Path) -> str | None:
    name = path.name
    # Match longer prefixes first so selected_meeting_ wins before meetings_.
    for prefix, table in sorted(PREFIX_TO_TABLE.items(), key=lambda item: len(item[0]), reverse=True):
        if name.startswith(prefix) and name.endswith(".json"):
            return table
    return None


def _read_json_records(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if data is None:
        return []
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unexpected JSON structure in {path}")


def _collect_raw_records() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(RAW_DIR.glob("*.json")):
        table = _table_for_file(path)
        if not table:
            print(f"Skipping unmatched raw file: {path.name}")
            continue
        records = _read_json_records(path)
        if not records:
            print(f"Skipping empty file: {path.name}")
            continue
        for record in records:
            if isinstance(record, dict):
                enriched = dict(record)
                enriched["source_file"] = path.name
                grouped[table].append(enriched)
    return grouped


def load_raw_json_to_sqlite() -> None:
    """Load all raw JSON files into SQLite raw_* tables.

    Raw tables are replaced on each run from the JSON files currently stored in
    data/raw/. This makes the database reproducible from the raw extraction
    layer and prevents duplicate raw rows after reruns.
    """
    ensure_project_dirs()
    schema_path = SQL_DIR / "schema.sql"
    if schema_path.exists():
        run_sql_file(schema_path)

    grouped = _collect_raw_records()
    if not grouped:
        raise ValueError("No raw JSON records found. Run extraction first or check data/raw/.")

    with get_connection(DB_PATH) as conn:
        for table, records in sorted(grouped.items()):
            df = pd.DataFrame(records)
            df = df.drop_duplicates()
            df.to_sql(table, conn, if_exists="replace", index=False)
            print(f"Loaded {len(df):>5} rows into {table}")
        conn.commit()

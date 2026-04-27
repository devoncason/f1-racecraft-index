from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Iterable

import pandas as pd

from src.analysis.calculate_racecraft_index import add_racecraft_index
from src.config import DB_PATH, PROJECT_DIR, TABLES_DIR, ensure_project_dirs
from src.db import get_connection, run_sql_file


def _read_table(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    try:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)
    except Exception:
        return pd.DataFrame()


def _as_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def _as_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _filter_session(df: pd.DataFrame, session_key: int | None) -> pd.DataFrame:
    if df.empty or session_key is None or "session_key" not in df.columns:
        return df.copy()
    return df[pd.to_numeric(df["session_key"], errors="coerce") == session_key].copy()


def _safe_bool_any(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    existing_cols = [col for col in cols if col in df.columns]
    if not existing_cols:
        return pd.Series([False] * len(df), index=df.index)
    return df[existing_cols].astype(str).apply(lambda col: col.str.lower().isin(["true", "1", "yes"])).any(axis=1)


def _agg_pit(pit: pd.DataFrame) -> pd.DataFrame:
    if pit.empty:
        return pd.DataFrame(columns=["driver_number", "total_pit_stops", "avg_pit_lane_duration", "avg_stop_duration"])
    pit = pit.copy()
    pit["lane_duration"] = _as_float(pit.get("lane_duration"))
    pit["stop_duration"] = _as_float(pit.get("stop_duration"))
    count_col = "lap_number" if "lap_number" in pit.columns else "date"
    return pit.groupby("driver_number", as_index=False).agg(
        total_pit_stops=(count_col, "count"),
        avg_pit_lane_duration=("lane_duration", "mean"),
        avg_stop_duration=("stop_duration", "mean"),
    )


def _agg_stints(stints: pd.DataFrame) -> pd.DataFrame:
    if stints.empty:
        return pd.DataFrame(columns=["driver_number", "total_stints", "longest_stint_laps"])
    stints = stints.copy()
    stints["lap_start"] = _as_float(stints.get("lap_start"))
    stints["lap_end"] = _as_float(stints.get("lap_end"))
    stints["stint_laps"] = stints["lap_end"] - stints["lap_start"] + 1
    count_col = "stint_number" if "stint_number" in stints.columns else "compound"
    return stints.groupby("driver_number", as_index=False).agg(
        total_stints=(count_col, "count"),
        longest_stint_laps=("stint_laps", "max"),
    )


def _agg_laps(laps: pd.DataFrame) -> pd.DataFrame:
    if laps.empty:
        return pd.DataFrame(columns=["driver_number", "avg_lap_time", "best_lap_time", "clean_lap_count"])
    laps = laps.copy()
    laps["lap_duration"] = _as_float(laps.get("lap_duration"))
    clean = laps.copy()
    for bool_col in ["is_pit_out_lap", "is_pit_in_lap"]:
        if bool_col in clean.columns:
            clean = clean[clean[bool_col].astype(str).str.lower() != "true"].copy()
    clean = clean.dropna(subset=["lap_duration"])
    if clean.empty:
        return pd.DataFrame(columns=["driver_number", "avg_lap_time", "best_lap_time", "clean_lap_count"])
    return clean.groupby("driver_number", as_index=False).agg(
        avg_lap_time=("lap_duration", "mean"),
        best_lap_time=("lap_duration", "min"),
        clean_lap_count=("lap_duration", "count"),
    )


def _agg_weather(weather: pd.DataFrame) -> tuple[int, float | None, float | None]:
    if weather.empty:
        return 0, None, None
    rainfall = _as_float(weather.get("rainfall", pd.Series(dtype=float))).fillna(0)
    avg_air_temp = _as_float(weather.get("air_temperature", pd.Series(dtype=float))).mean()
    avg_track_temp = _as_float(weather.get("track_temperature", pd.Series(dtype=float))).mean()
    wet_flag = int((rainfall > 0).any())
    return wet_flag, avg_air_temp, avg_track_temp


def _agg_race_control(race_control: pd.DataFrame) -> tuple[int, int, int, int]:
    if race_control.empty:
        return 0, 0, 0, 0
    text = (
        race_control.get("category", pd.Series(dtype=str)).fillna("").astype(str) + " "
        + race_control.get("message", pd.Series(dtype=str)).fillna("").astype(str) + " "
        + race_control.get("flag", pd.Series(dtype=str)).fillna("").astype(str)
    ).str.upper()
    safety_car_flag = int(text.str.contains("SAFETY CAR", regex=False).any())
    vsc_flag = int(text.str.contains("VIRTUAL SAFETY CAR", regex=False).any() or text.str.contains(" VSC", regex=False).any())
    red_flag = int(text.str.contains("RED", regex=False).any())
    incident_count = int(len(race_control))
    return safety_car_flag, vsc_flag, red_flag, incident_count


def _agg_overtakes(overtakes: pd.DataFrame) -> pd.DataFrame:
    expected = {"overtaking_driver_number", "overtaken_driver_number"}
    if overtakes.empty or not expected.issubset(overtakes.columns):
        return pd.DataFrame(columns=["driver_number", "overtakes_made", "overtaken_count"])
    made = overtakes.groupby("overtaking_driver_number").size().rename("overtakes_made").reset_index()
    made = made.rename(columns={"overtaking_driver_number": "driver_number"})
    taken = overtakes.groupby("overtaken_driver_number").size().rename("overtaken_count").reset_index()
    taken = taken.rename(columns={"overtaken_driver_number": "driver_number"})
    return pd.merge(made, taken, on="driver_number", how="outer").fillna(0)


def _select_qualifying_session(sessions: pd.DataFrame, meeting_key: int) -> int | None:
    if sessions.empty or "meeting_key" not in sessions.columns or "session_name" not in sessions.columns:
        return None
    subset = sessions[pd.to_numeric(sessions["meeting_key"], errors="coerce") == meeting_key].copy()
    subset = subset[subset["session_name"].astype(str).str.lower().str.contains("qualifying", na=False)]
    if subset.empty:
        return None
    return int(subset.iloc[0]["session_key"])


def _meeting_lookup(meetings: pd.DataFrame, meeting_key: int) -> dict:
    if meetings.empty or "meeting_key" not in meetings.columns:
        return {}
    subset = meetings[pd.to_numeric(meetings["meeting_key"], errors="coerce") == meeting_key]
    if subset.empty:
        return {}
    return subset.iloc[0].to_dict()


def _build_one_race(
    *,
    race_session_row: pd.Series,
    tables: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    race_session_key = int(race_session_row["session_key"])
    meeting_key = int(race_session_row["meeting_key"])
    qualifying_session_key = _select_qualifying_session(tables["sessions"], meeting_key)
    meeting = _meeting_lookup(tables["meetings"], meeting_key)

    drivers = _filter_session(tables["drivers"], race_session_key)
    quali = _filter_session(tables["quali"], qualifying_session_key)
    grid = _filter_session(tables["grid"], race_session_key)
    race = _filter_session(tables["race"], race_session_key)
    pit = _filter_session(tables["pit"], race_session_key)
    stints = _filter_session(tables["stints"], race_session_key)
    laps = _filter_session(tables["laps"], race_session_key)
    weather = _filter_session(tables["weather"], race_session_key)
    race_control = _filter_session(tables["race_control"], race_session_key)
    overtakes = _filter_session(tables["overtakes"], race_session_key)

    if race.empty:
        print(f"Warning: raw_race_result is empty for session {race_session_key}; skipping.")
        return pd.DataFrame()

    base_cols = [col for col in ["driver_number", "position", "dnf", "dns", "dsq", "points"] if col in race.columns]
    features = race[base_cols].copy()
    features = features.rename(columns={"position": "finish_position"})
    features["driver_number"] = _as_int(features["driver_number"])
    features["finish_position"] = _as_int(features["finish_position"])

    if not quali.empty and {"driver_number", "position"}.issubset(quali.columns):
        q = quali[["driver_number", "position"]].rename(columns={"position": "quali_position"})
        q["driver_number"] = _as_int(q["driver_number"])
        q["quali_position"] = _as_int(q["quali_position"])
        features = features.merge(q, on="driver_number", how="left")
    else:
        features["quali_position"] = pd.NA

    if not grid.empty and {"driver_number", "position"}.issubset(grid.columns):
        g = grid[["driver_number", "position"]].rename(columns={"position": "grid_position"})
        g["driver_number"] = _as_int(g["driver_number"])
        g["grid_position"] = _as_int(g["grid_position"])
        features = features.merge(g, on="driver_number", how="left")
        features["grid_source"] = "starting_grid"
    else:
        features["grid_position"] = features["quali_position"]
        features["grid_source"] = "qualifying_result_fallback"

    if not drivers.empty and "driver_number" in drivers.columns:
        driver_name_col = "full_name" if "full_name" in drivers.columns else "broadcast_name"
        keep_cols = ["driver_number"]
        if driver_name_col in drivers.columns:
            keep_cols.append(driver_name_col)
        if "team_name" in drivers.columns:
            keep_cols.append("team_name")
        d = drivers[keep_cols].drop_duplicates()
        d["driver_number"] = _as_int(d["driver_number"])
        features = features.merge(d, on="driver_number", how="left")
        features = features.rename(columns={driver_name_col: "driver_name"})

    for agg in [_agg_pit(pit), _agg_stints(stints), _agg_laps(laps), _agg_overtakes(overtakes)]:
        if not agg.empty:
            agg["driver_number"] = _as_int(agg["driver_number"])
            features = features.merge(agg, on="driver_number", how="left")

    features["positions_gained_vs_quali"] = features["quali_position"] - features["finish_position"]
    features["positions_gained_vs_grid"] = features["grid_position"] - features["finish_position"]

    wet_flag, avg_air_temp, avg_track_temp = _agg_weather(weather)
    safety_car_flag, vsc_flag, red_flag, incident_count = _agg_race_control(race_control)
    features["weather_wet_flag"] = wet_flag
    features["avg_air_temperature"] = avg_air_temp
    features["avg_track_temperature"] = avg_track_temp
    features["safety_car_flag"] = safety_car_flag
    features["vsc_flag"] = vsc_flag
    features["red_flag"] = red_flag
    features["race_control_incident_count"] = incident_count
    features["finished_flag"] = (~_safe_bool_any(features, ["dnf", "dns", "dsq"])).astype(int)

    features["season_year"] = int(meeting.get("year") or race_session_row.get("year"))
    features["meeting_key"] = meeting_key
    features["meeting_name"] = meeting.get("meeting_name") or race_session_row.get("meeting_name")
    features["country_name"] = meeting.get("country_name") or race_session_row.get("country_name")
    features["location"] = meeting.get("location") or race_session_row.get("location")
    features["race_session_key"] = race_session_key
    features["qualifying_session_key"] = qualifying_session_key
    features["session_date_start"] = race_session_row.get("date_start")

    features["context_label"] = features.apply(
        lambda row: "wet" if row["weather_wet_flag"] == 1 else "dry",
        axis=1,
    )
    features["context_label"] = features["context_label"] + features.apply(
        lambda row: "_safety_car" if row["safety_car_flag"] == 1 else ("_vsc" if row["vsc_flag"] == 1 else "_no_sc"),
        axis=1,
    )
    features["extraction_timestamp_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for col in ["total_pit_stops", "total_stints", "overtakes_made", "overtaken_count", "clean_lap_count"]:
        if col in features.columns:
            features[col] = _as_int(features[col].fillna(0))

    features = add_racecraft_index(features)
    return features


def build_race_driver_features() -> pd.DataFrame:
    """Build and persist one combined driver-race feature table across weekends."""
    ensure_project_dirs()
    run_sql_file(PROJECT_DIR / "sql" / "schema.sql")

    with get_connection(DB_PATH) as conn:
        tables = {
            "meetings": _read_table(conn, "raw_meetings"),
            "sessions": _read_table(conn, "raw_sessions"),
            "drivers": _read_table(conn, "raw_drivers"),
            "quali": _read_table(conn, "raw_qualifying_result"),
            "grid": _read_table(conn, "raw_starting_grid"),
            "race": _read_table(conn, "raw_race_result"),
            "pit": _read_table(conn, "raw_pit"),
            "stints": _read_table(conn, "raw_stints"),
            "laps": _read_table(conn, "raw_laps"),
            "weather": _read_table(conn, "raw_weather"),
            "race_control": _read_table(conn, "raw_race_control"),
            "overtakes": _read_table(conn, "raw_overtakes"),
        }
        race_sessions = _read_table(conn, "raw_selected_race_session")

        if race_sessions.empty:
            raise ValueError("raw_selected_race_session is empty. Extraction did not pull race sessions.")

        all_features = []
        for _, race_session_row in race_sessions.drop_duplicates(subset=["session_key"]).iterrows():
            one_race = _build_one_race(race_session_row=race_session_row, tables=tables)
            if not one_race.empty:
                all_features.append(one_race)

        if not all_features:
            raise ValueError("No race_driver_features rows were created.")

        features = pd.concat(all_features, ignore_index=True)

        final_cols = [
            "season_year", "meeting_key", "meeting_name", "country_name", "location",
            "race_session_key", "qualifying_session_key", "session_date_start", "driver_number",
            "driver_name", "team_name", "quali_position", "grid_position", "grid_source", "finish_position",
            "positions_gained_vs_quali", "positions_gained_vs_grid", "total_pit_stops",
            "avg_pit_lane_duration", "avg_stop_duration", "longest_stint_laps", "total_stints",
            "avg_lap_time", "best_lap_time", "clean_lap_count", "weather_wet_flag",
            "avg_air_temperature", "avg_track_temperature", "safety_car_flag", "vsc_flag", "red_flag",
            "race_control_incident_count", "overtakes_made", "overtaken_count", "net_overtakes",
            "pit_stop_delta_to_race_avg", "points", "finished_flag", "context_label",
            "racecraft_index_mvp", "racecraft_tier", "extraction_timestamp_utc",
        ]
        for col in final_cols:
            if col not in features.columns:
                features[col] = pd.NA
        features = features[final_cols]

        session_keys = sorted(features["race_session_key"].dropna().astype(int).unique().tolist())
        placeholders = ",".join("?" for _ in session_keys)
        if session_keys:
            conn.execute(f"DELETE FROM race_driver_features WHERE race_session_key IN ({placeholders})", session_keys)
        features.to_sql("race_driver_features", conn, if_exists="append", index=False)
        conn.commit()

    output_csv = TABLES_DIR / "race_driver_features.csv"
    features.to_csv(output_csv, index=False)
    print(f"Saved feature table to {output_csv}")

    preview_cols = [
        "season_year", "meeting_name", "driver_name", "team_name", "grid_position",
        "finish_position", "positions_gained_vs_grid", "racecraft_index_mvp", "racecraft_tier",
    ]
    print(features.sort_values("racecraft_index_mvp", ascending=False)[preview_cols].head(20))
    return features


if __name__ == "__main__":
    build_race_driver_features()

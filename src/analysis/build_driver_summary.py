import pandas as pd

from src.config import DB_PATH, TABLES_DIR, ensure_project_dirs
from src.db import get_connection, run_sql_file
from src.config import PROJECT_DIR


def build_driver_context_summary() -> pd.DataFrame:
    """Aggregate driver performance across the currently processed race weekends."""
    ensure_project_dirs()
    run_sql_file(PROJECT_DIR / "sql" / "schema.sql")

    with get_connection(DB_PATH) as conn:
        try:
            df = pd.read_sql_query("SELECT * FROM race_driver_features", conn)
        except Exception:
            df = pd.DataFrame()

        if df.empty:
            raise ValueError("race_driver_features is empty. Build features before summary tables.")

        numeric_cols = [
            "finish_position", "grid_position", "positions_gained_vs_grid", "positions_gained_vs_quali",
            "racecraft_index_mvp", "overtakes_made", "overtaken_count", "net_overtakes",
            "total_pit_stops", "finished_flag", "weather_wet_flag", "safety_car_flag", "vsc_flag",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        summary = df.groupby(["season_year", "driver_name", "team_name"], dropna=False).agg(
            race_count=("race_session_key", "nunique"),
            avg_grid_position=("grid_position", "mean"),
            avg_finish_position=("finish_position", "mean"),
            total_positions_gained_vs_grid=("positions_gained_vs_grid", "sum"),
            avg_positions_gained_vs_grid=("positions_gained_vs_grid", "mean"),
            avg_racecraft_index=("racecraft_index_mvp", "mean"),
            best_racecraft_index=("racecraft_index_mvp", "max"),
            worst_racecraft_index=("racecraft_index_mvp", "min"),
            total_overtakes_made=("overtakes_made", "sum"),
            total_overtaken_count=("overtaken_count", "sum"),
            avg_pit_stops=("total_pit_stops", "mean"),
            finish_rate=("finished_flag", "mean"),
            wet_race_count=("weather_wet_flag", "sum"),
            safety_car_race_count=("safety_car_flag", "sum"),
        ).reset_index()

        summary = summary.sort_values(["season_year", "avg_racecraft_index"], ascending=[True, False])
        summary.to_sql("driver_context_summary", conn, if_exists="replace", index=False)
        conn.commit()

    output = TABLES_DIR / "driver_context_summary.csv"
    summary.to_csv(output, index=False)
    print(f"Saved driver summary to {output}")
    return summary


if __name__ == "__main__":
    build_driver_context_summary()

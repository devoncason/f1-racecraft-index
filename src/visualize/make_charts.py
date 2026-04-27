from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.config import DB_PATH, FIGURES_DIR, ensure_project_dirs
from src.db import get_connection
from src.extract.openf1_client import safe_slug


def _load_features() -> pd.DataFrame:
    with get_connection(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM race_driver_features", conn)
    if df.empty:
        raise ValueError("race_driver_features is empty. Run the pipeline first.")
    for col in ["positions_gained_vs_grid", "racecraft_index_mvp", "season_year", "race_session_key"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _save_current_figure(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()
    print(f"Saved chart to {output}")


def make_position_delta_charts(df: pd.DataFrame) -> None:
    """Create one positions gained/lost chart per race weekend."""
    required = {"race_session_key", "driver_name", "positions_gained_vs_grid", "meeting_name", "season_year"}
    if not required.issubset(df.columns):
        print("Skipping position delta charts because required columns are missing.")
        return

    clean = df.dropna(subset=["positions_gained_vs_grid"]).copy()
    for race_session_key, race_df in clean.groupby("race_session_key"):
        race_df = race_df.sort_values("positions_gained_vs_grid")
        season = int(race_df["season_year"].iloc[0])
        meeting = str(race_df["meeting_name"].iloc[0])

        plt.figure(figsize=(10, 8))
        plt.barh(race_df["driver_name"], race_df["positions_gained_vs_grid"])
        plt.axvline(0, linewidth=1)
        plt.title(f"Positions Gained/Lost vs Starting Grid - {season} {meeting}")
        plt.xlabel("Grid position - finish position")
        plt.ylabel("Driver")
        output = FIGURES_DIR / f"positions_gained_vs_grid_{season}_{safe_slug(meeting)}.png"
        _save_current_figure(output)


def make_top_racecraft_chart(df: pd.DataFrame, top_n: int = 15) -> None:
    if "racecraft_index_mvp" not in df.columns:
        print("Skipping top Racecraft Index chart because racecraft_index_mvp is missing.")
        return

    summary = df.groupby("driver_name", dropna=False).agg(
        avg_racecraft_index=("racecraft_index_mvp", "mean"),
        race_count=("race_session_key", "nunique"),
    ).reset_index()
    summary = summary.sort_values("avg_racecraft_index", ascending=False).head(top_n)
    summary = summary.sort_values("avg_racecraft_index")

    plt.figure(figsize=(10, 7))
    plt.barh(summary["driver_name"], summary["avg_racecraft_index"])
    plt.axvline(0, linewidth=1)
    plt.title("Average Racecraft Index by Driver")
    plt.xlabel("Average Racecraft Index MVP")
    plt.ylabel("Driver")
    _save_current_figure(FIGURES_DIR / "top_racecraft_index.png")


def make_context_average_chart(df: pd.DataFrame) -> None:
    required = {"context_label", "racecraft_index_mvp"}
    if not required.issubset(df.columns):
        print("Skipping context chart because required columns are missing.")
        return

    context = df.groupby("context_label", dropna=False).agg(
        avg_racecraft_index=("racecraft_index_mvp", "mean"),
        driver_race_rows=("racecraft_index_mvp", "count"),
    ).reset_index()
    context = context.sort_values("avg_racecraft_index")

    plt.figure(figsize=(10, 6))
    plt.barh(context["context_label"], context["avg_racecraft_index"])
    plt.axvline(0, linewidth=1)
    plt.title("Average Racecraft Index by Race Context")
    plt.xlabel("Average Racecraft Index MVP")
    plt.ylabel("Race context")
    _save_current_figure(FIGURES_DIR / "context_average_racecraft.png")


def make_all_charts() -> None:
    ensure_project_dirs()
    df = _load_features()
    make_position_delta_charts(df)
    make_top_racecraft_chart(df)
    make_context_average_chart(df)


if __name__ == "__main__":
    make_all_charts()

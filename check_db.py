from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "processed" / "f1_racecraft.sqlite"

if not DB_PATH.exists():
    raise FileNotFoundError(
        f"Database not found at: {DB_PATH}\n"
        "Run this first: .\\.venv\\Scripts\\python.exe main.py --skip-fetch"
    )

with sqlite3.connect(DB_PATH) as con:
    print("\nDATABASE TABLES")
    print("-" * 60)

    tables = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    for table in tables:
        print(table[0])

    print("\nROW COUNTS")
    print("-" * 60)

    key_tables = [
        "raw_drivers",
        "raw_qualifying_result",
        "raw_race_result",
        "raw_laps",
        "raw_pit",
        "raw_stints",
        "raw_weather",
        "race_driver_features",
    ]

    for table in key_tables:
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")

    print("\nTOP RACECRAFT RESULTS")
    print("-" * 60)

    df = pd.read_sql_query(
        """
        SELECT
            season_year,
            meeting_name,
            driver_name,
            team_name,
            grid_position,
            finish_position,
            positions_gained_vs_grid,
            racecraft_index_mvp,
            racecraft_tier
        FROM race_driver_features
        ORDER BY racecraft_index_mvp DESC
        LIMIT 10
        """,
        con,
    )

    print(df.to_string(index=False))

import argparse
import sys
from pathlib import Path

import pandas as pd

from src.analysis.build_driver_summary import build_driver_context_summary
from src.analysis.build_race_driver_features import build_race_driver_features
from src.config import ensure_project_dirs
from src.extract.fetch_weekend import fetch_season, fetch_weekend
from src.transform.load_raw_to_sqlite import load_raw_json_to_sqlite
from src.visualize.make_charts import make_all_charts


def _split_csv_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _run_fetch(args: argparse.Namespace) -> None:
    """Fetch raw OpenF1 JSON files according to CLI arguments."""
    if args.skip_fetch:
        print("Skipping API fetch. Reusing existing files in data/raw/.")
        return

    if args.weekends_csv:
        csv_path = Path(args.weekends_csv)
        if not csv_path.exists():
            raise FileNotFoundError(f"Weekend CSV not found: {csv_path}")
        weekends = pd.read_csv(csv_path)
        required = {"year", "country"}
        if not required.issubset(weekends.columns):
            raise ValueError("Weekend CSV must contain at least these columns: year, country")

        for _, row in weekends.iterrows():
            meeting_name = row.get("meeting_name") if "meeting_name" in weekends.columns else None
            if pd.isna(meeting_name):
                meeting_name = None
            fetch_weekend(int(row["year"]), str(row["country"]), meeting_name=meeting_name)
        return

    if args.season:
        fetch_season(args.season, max_weekends=args.max_weekends)
        return

    if args.year and args.countries:
        countries = _split_csv_values(args.countries)
        if not countries:
            raise ValueError("--countries was provided, but no countries were parsed.")
        for country in countries:
            fetch_weekend(args.year, country)
        return

    if args.year and args.country:
        fetch_weekend(args.year, args.country, meeting_name=args.meeting_name)
        return

    raise ValueError(
        "Choose one fetch mode: --year + --country, --year + --countries, "
        "--season, --weekends-csv, or --skip-fetch."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the F1 Racecraft Index dataset and charts.")
    parser.add_argument("--year", type=int, help="Season year for a single or selected set of race weekends.")
    parser.add_argument("--country", type=str, help="Country name for one race weekend, such as Singapore or Monaco.")
    parser.add_argument("--meeting-name", type=str, help="Optional meeting name filter for countries with multiple races.")
    parser.add_argument("--countries", type=str, help="Comma-separated countries or meeting names to fetch for one year.")
    parser.add_argument("--season", type=int, help="Fetch every available race meeting for a season year.")
    parser.add_argument("--max-weekends", type=int, help="Optional limit when testing a full-season pull.")
    parser.add_argument("--weekends-csv", type=str, help="CSV file with year,country,optional meeting_name columns.")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip API fetch and rebuild from existing raw JSON files.")
    parser.add_argument("--skip-charts", action="store_true", help="Build tables but skip chart generation.")

    args = parser.parse_args()

    try:
        ensure_project_dirs()
        _run_fetch(args)

        print("Loading raw JSON into SQLite...")
        load_raw_json_to_sqlite()

        print("Building race_driver_features...")
        build_race_driver_features()

        print("Building driver context summary...")
        build_driver_context_summary()

        if not args.skip_charts:
            print("Making charts...")
            make_all_charts()

        print("Done. Check data/processed/, reports/tables/, and reports/figures/.")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()

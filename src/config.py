from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
SQL_DIR = PROJECT_DIR / "sql"
DB_PATH = PROCESSED_DATA_DIR / "f1_racecraft.sqlite"

# Backward-compatible aliases used by older versions of the starter files.
RAW_DIR = RAW_DATA_DIR
PROCESSED_DIR = PROCESSED_DATA_DIR


def ensure_project_dirs() -> None:
    """Create local output folders if they do not already exist."""
    for path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR, TABLES_DIR, SQL_DIR]:
        path.mkdir(parents=True, exist_ok=True)

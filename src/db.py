import sqlite3
from pathlib import Path

from src.config import DB_PATH, ensure_project_dirs


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Return a SQLite connection with dictionary-like row support."""
    ensure_project_dirs()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def run_sql_file(sql_path: Path, db_path: Path = DB_PATH) -> None:
    """Execute a SQL file against the project SQLite database."""
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    with get_connection(db_path) as conn:
        conn.executescript(sql_path.read_text(encoding="utf-8"))
        conn.commit()

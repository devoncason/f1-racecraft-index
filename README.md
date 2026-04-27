# F1 Racecraft Index

A Python data pipeline for pulling Formula 1 race-weekend data from the OpenF1 API, storing it in SQLite, building driver-level race features, and creating repeatable analysis outputs for overperformance and underperformance across race contexts.

This project is built around one core question:

> Why did a driver or team overperform or underperform on a given race weekend?

The current version focuses on a transparent MVP metric, the **Racecraft Index**, using available weekend-level variables such as starting position, finishing position, qualifying position, overtakes, pit-stop activity, weather, safety-car context, and race-control events. The goal is not to claim a perfect performance model. The goal is to build a clean, explainable, expandable analytics pipeline that can support deeper portfolio-quality Formula 1 analysis over time.

---

## What this project does

The pipeline can:

1. Pull OpenF1 data for one race weekend, multiple selected weekends, or a full season.
2. Save raw API responses as JSON files for traceability.
3. Load raw JSON files into a local SQLite database.
4. Build a combined `race_driver_features` table across all processed weekends.
5. Calculate driver-level overperformance and underperformance indicators.
6. Save summary tables as CSV files.
7. Generate charts for race-level and multi-race comparison.

---

## Project structure

```text
f1-racecraft-index/
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── sql/
│   └── schema.sql
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── extract/
│   │   ├── __init__.py
│   │   ├── openf1_client.py
│   │   └── fetch_weekend.py
│   ├── transform/
│   │   ├── __init__.py
│   │   └── load_raw_to_sqlite.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── build_race_driver_features.py
│   │   ├── build_driver_summary.py
│   │   └── calculate_racecraft_index.py
│   └── visualize/
│       ├── __init__.py
│       └── make_charts.py
├── docs/
│   └── runbook.md
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   └── processed/
│       └── .gitkeep
└── reports/
    ├── figures/
    │   └── .gitkeep
    └── tables/
        └── .gitkeep
```

Generated raw data, database files, charts, and CSV exports are ignored by Git by default so the repository stays clean.

---

## Setup

From the project folder:

```powershell
python --version
python -m venv .venv
```

If PowerShell blocks virtual environment activation on a work computer, use this temporary session-only command:

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& ".\.venv\Scripts\Activate.ps1")
```

Then install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If activation is blocked or you prefer not to activate the environment, run commands through the virtual environment Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py --year 2024 --country Singapore
```

---

## Usage

### Run one race weekend

```powershell
python main.py --year 2024 --country Singapore
```

You can replace the year and country with the race weekend you want to analyze:

```powershell
python main.py --year 2023 --country Italy
python main.py --year 2024 --country Monaco
python main.py --year 2024 --country Japan
```

For countries with more than one Grand Prix in the same season, add a meeting name to avoid ambiguity:

```powershell
python main.py --year 2024 --country United States --meeting-name Miami
```

### Run multiple countries for the same year

```powershell
python main.py --year 2024 --countries "Bahrain,Saudi Arabia,Australia,Japan,China,Miami,Monaco,Canada,Spain"
```

### Run a full season

```powershell
python main.py --season 2024
```

### Run from a CSV list of weekends

Create a CSV file with columns named `year`, `country`, and optionally `meeting_name`:

```csv
year,country,meeting_name
2024,Singapore,
2024,United States,Miami
2024,Italy,Monza
```

Then run:

```powershell
python main.py --weekends-csv data/weekends_to_pull.csv
```

### Rebuild database and charts from already downloaded raw JSON

```powershell
python main.py --skip-fetch
```

---

## Main outputs

After a successful run, the project creates:

```text
data/raw/                       Raw JSON files from OpenF1
data/processed/f1_racecraft.sqlite   SQLite database
reports/tables/race_driver_features.csv
reports/tables/driver_context_summary.csv
reports/figures/positions_gained_vs_grid_*.png
reports/figures/top_racecraft_index.png
reports/figures/context_average_racecraft.png
```

The most important table is `race_driver_features`. It stores one row per driver per race weekend and can grow across multiple weekends or seasons.

---

## Racecraft Index MVP

The current Racecraft Index is intentionally simple and transparent. It combines:

- positions gained or lost versus starting grid
- positions gained or lost versus qualifying
- net overtakes
- pit-stop count compared with the race average
- finishing status

The index should be treated as a first-pass signal, not a final truth. It is useful for surfacing which drivers deserve closer investigation, especially when combined with context variables such as weather, safety-car activity, pit strategy, team, and race-control events.

---

## Important note about starting grid data

Some OpenF1 weekends may not return data from the `starting_grid` endpoint. When that happens, this project uses qualifying position as the fallback grid position and marks the grid source as `qualifying_result_fallback`.

That fallback keeps the pipeline running, but it is not perfect. Real starting grids can differ from qualifying order because of penalties, pit-lane starts, parc fermé changes, or other race-specific conditions. This is documented in the output through the `grid_source` column.

---

## Portfolio direction

This project is designed to be expandable. Strong next improvements include:

- comparing Racecraft Index by team, driver, and season
- adding track-type context when a reliable track-classification source is available
- separating sprint weekends from standard weekends
- improving the index with pace-adjusted metrics
- adding qualifying-to-race conversion analysis
- building an interactive dashboard
- validating results against race reports and stewarding context

---

## Data source

This project uses publicly available Formula 1 data from the OpenF1 API.


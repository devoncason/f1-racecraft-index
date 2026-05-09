# F1 Racecraft Index

A Python data pipeline for pulling Formula 1 race-weekend data from the OpenF1 API, storing it in SQLite, building driver-level race features, and creating repeatable analysis outputs for overperformance and underperformance across race contexts.

This project is built around one core question:

> Which drivers appeared to overperform or underperform on a Formula 1 race weekend, and what race-context signals help explain the result?

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

## Skills demonstrated

This project demonstrates:

- API data ingestion from OpenF1
- JSON extraction and local raw-data storage
- SQLite database design and loading
- Python data transformation with pandas
- Driver-level feature engineering
- Repeatable command-line workflows
- CSV output generation
- Matplotlib visualization
- Documentation, methodology notes, and reproducible project structure

---

## Example output

Test case: **2024 Singapore Grand Prix**

![Successful terminal run](docs/assets/successful_run.png)

![Database verification output](docs/assets/check_db_output.png)

![Sample Racecraft chart](docs/assets/sample_chart.png)

Top Racecraft Index results from the first MVP model:

| Driver | Team | Grid | Finish | Positions Gained | Racecraft Index | Tier |
|---|---:|---:|---:|---:|---:|---|
| ZHOU Guanyu | Kick Sauber | 20 | 15 | 5 | 16.36 | strong_overperformance |
| Charles LECLERC | Ferrari | 9 | 5 | 4 | 14.11 | strong_overperformance |
| Sergio PEREZ | Red Bull Racing | 13 | 10 | 3 | 9.86 | strong_overperformance |

---

## Project structure

```text
f1-racecraft-index/
├── main.py
├── check_db.py
├── requirements.txt
├── README.md
├── .gitignore
├── sql/
│   └── schema.sql
├── src/
│   ├── config.py
│   ├── db.py
│   ├── extract/
│   │   ├── openf1_client.py
│   │   └── fetch_weekend.py
│   ├── transform/
│   │   └── load_raw_to_sqlite.py
│   ├── analysis/
│   │   ├── build_race_driver_features.py
│   │   ├── build_driver_summary.py
│   │   └── calculate_racecraft_index.py
│   └── visualize/
│       └── make_charts.py
├── docs/
│   ├── runbook.md
│   ├── data_dictionary.md
│   ├── methodology.md
│   └── assets/
│       ├── successful_run.png
│       ├── check_db_output.png
│       └── sample_chart.png
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

If PowerShell blocks virtual environment activation on a work computer, use the virtual environment Python directly instead of activating it:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If activation works on your computer, you can also use:

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& ".\.venv\Scripts\Activate.ps1")
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Usage

### Run one race weekend

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --country Singapore
```

You can replace the year and country with the race weekend you want to analyze:

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --country Monaco
.\.venv\Scripts\python.exe main.py --year 2024 --country Japan
.\.venv\Scripts\python.exe main.py --year 2024 --country Canada
```

For countries with more than one Grand Prix in the same season, add a meeting name to avoid ambiguity:

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --country United States --meeting-name Miami
```

### Run multiple countries for the same year

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --countries "Bahrain,Saudi Arabia,Australia,Japan,Monaco,Canada"
```

### Run a full season

```powershell
.\.venv\Scripts\python.exe main.py --season 2024
```

### Rebuild database and charts from already downloaded raw JSON

```powershell
.\.venv\Scripts\python.exe main.py --skip-fetch
```

---

## Main outputs

After a successful run, the project creates:

```text
data/raw/                             Raw JSON files from OpenF1
data/processed/f1_racecraft.sqlite   SQLite database
reports/tables/race_driver_features.csv
reports/tables/driver_context_summary.csv
reports/figures/positions_gained_vs_grid_*.png
reports/figures/top_racecraft_index.png
reports/figures/context_average_racecraft.png
```

The most important table is `race_driver_features`. It stores one row per driver per race weekend and can grow across multiple weekends or seasons.

---

## Verify the database

After running the pipeline, confirm that the SQLite database and output tables were created:

```powershell
.\.venv\Scripts\python.exe check_db.py
```

---

## Racecraft Index MVP

The current Racecraft Index is intentionally simple and transparent. It combines:

- positions gained or lost versus starting grid
- positions gained or lost versus qualifying
- net overtakes
- pit-stop count compared with the race average
- finishing status

The index should be treated as a first-pass signal, not a final truth. It is useful for surfacing which drivers deserve closer investigation, especially when combined with context variables such as weather, safety-car activity, pit strategy, team, and race-control events.

For details, see:

- [`docs/methodology.md`](docs/methodology.md)
- [`docs/data_dictionary.md`](docs/data_dictionary.md)
- [`docs/runbook.md`](docs/runbook.md)

---

## Known limitations

This project is an MVP portfolio model, not a definitive driver-rating system. Some OpenF1 endpoints are not populated for every weekend. For example, if starting grid data is unavailable, the current pipeline falls back to qualifying result position as a proxy for grid position. That means grid penalties, pit-lane starts, and post-qualifying changes may not be fully captured yet.

The current Racecraft Index is intentionally transparent and explainable. It highlights drivers worth deeper review, but future versions should add stronger pace normalization, teammate comparison, tire degradation, safety car timing, strategy windows, and team baseline performance.

---

## Important note about starting grid data

Some OpenF1 weekends may not return data from the `starting_grid` endpoint. When that happens, this project uses qualifying position as the fallback grid position and marks the grid source as `qualifying_result_fallback`.

That fallback keeps the pipeline running, but it is not perfect. Real starting grids can differ from qualifying order because of penalties, pit-lane starts, parc fermé changes, or other race-specific conditions. This is documented in the output through the `grid_source` column.

---

## Portfolio context

This repository is my first public Formula 1 analytics portfolio project and was built as a capstone-style Python data pipeline. It focuses on creating a clean, explainable Racecraft Index MVP.

A future companion project, `f1-racecraft-intelligence`, will build on this foundation with deeper season-level, circuit-level, and context-aware analysis.

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

This project uses publicly available Formula 1 data from the [OpenF1 API](https://openf1.org/).

---

## Disclaimer

This repository is an independent educational and portfolio project. It is not affiliated with, endorsed by, sponsored by, or associated with Formula 1, Formula One Management, Formula One Licensing B.V., the FIA, OpenF1, any Formula 1 team, or any Formula 1 driver.

Formula 1, F1, FIA Formula One World Championship, Grand Prix names, team names, driver names, circuit names, logos, and related marks are trademarks or property of their respective owners. This project does not claim ownership of any trademarks, logos, race footage, photographs, proprietary timing systems, or official Formula 1 materials.

The analysis is based on publicly available/unofficial API data and is intended for learning, analytics practice, and portfolio demonstration only.

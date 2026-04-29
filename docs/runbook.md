# F1 Racecraft Index Runbook

This runbook is the practical step-by-step guide for running, verifying, resetting, and testing the project locally in VS Code or in Replit.

---

## 1. Open the project folder

Open VS Code and choose the folder named:

```text
f1-racecraft-index
```

The project root should contain:

```text
README.md
main.py
check_db.py
requirements.txt
src/
sql/
data/
docs/
reports/
```

Do not open a parent folder like `py4e/` if you are trying to run this project. Open the actual repository folder.

---

## 2. Open the VS Code terminal

In VS Code:

```text
Terminal > New Terminal
```

Confirm you are in the project folder:

```powershell
pwd
```

You should see a path ending in:

```text
f1-racecraft-index
```

---

## 3. Create the virtual environment

Run:

```powershell
python -m venv .venv
```

This creates a local Python environment inside the project folder.

---

## 4. Install dependencies

Because some work computers block PowerShell activation scripts, the safest pattern is to use the virtual environment Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If activation works on your machine, this is also fine:

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& ".\.venv\Scripts\Activate.ps1")
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The direct `.venv\Scripts\python.exe` method is the most reliable option on a restricted work PC.

---

## 5. Run the known-good test case

Use the Singapore 2024 race weekend as the first validation test:

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --country Singapore
```

A successful run should:

1. Pull OpenF1 data.
2. Save raw JSON files into `data/raw/`.
3. Build the SQLite database at `data/processed/f1_racecraft.sqlite`.
4. Build `race_driver_features`.
5. Export CSV files into `reports/tables/`.
6. Generate PNG charts into `reports/figures/`.

---

## 6. Verify the database

After the main program finishes, run:

```powershell
.\.venv\Scripts\python.exe check_db.py
```

This confirms that the database exists and that important tables were created.

Important output files to check:

```text
data/processed/f1_racecraft.sqlite
reports/tables/race_driver_features.csv
reports/tables/driver_context_summary.csv
reports/figures/
```

---

## 7. Rebuild from existing raw data without calling the API

If you already have JSON files in `data/raw/` and only want to rebuild the database, tables, and charts, run:

```powershell
.\.venv\Scripts\python.exe main.py --skip-fetch
```

Use this when:

- you changed transformation logic
- you changed Racecraft Index calculations
- you changed chart logic
- you want to avoid pulling the same API data again

---

## 8. Run a different single race weekend

Change the year and country:

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --country Monaco
.\.venv\Scripts\python.exe main.py --year 2024 --country Japan
.\.venv\Scripts\python.exe main.py --year 2024 --country Canada
```

For countries with multiple Grand Prix weekends in the same season, add a meeting name:

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --country United States --meeting-name Miami
```

The `country` value should match the OpenF1 meeting country name. The `meeting-name` value helps narrow the selection when a country hosts more than one race weekend.

---

## 9. Run several selected race weekends

Use a comma-separated list:

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --countries "Bahrain,Saudi Arabia,Australia,Japan,Monaco,Canada"
```

This is useful for testing multi-race output without pulling a full season.

---

## 10. Run a full season

```powershell
.\.venv\Scripts\python.exe main.py --season 2024
```

For a smaller test run:

```powershell
.\.venv\Scripts\python.exe main.py --season 2024 --max-weekends 3
```

Run the smaller test first before running a full season.

---

## 11. Reset the project outputs

Use this when you want to clear generated files and run the pipeline fresh.

### PowerShell reset command

```powershell
Remove-Item data\raw\*.json -Force -ErrorAction SilentlyContinue
Remove-Item data\processed\*.sqlite -Force -ErrorAction SilentlyContinue
Remove-Item reports\tables\*.csv -Force -ErrorAction SilentlyContinue
Remove-Item reports\figures\*.png -Force -ErrorAction SilentlyContinue
```

Then rerun the known-good test:

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --country Singapore
.\.venv\Scripts\python.exe check_db.py
```

Do not delete the `.gitkeep` files. They keep empty folders visible in GitHub.

---

## 12. Reset and rebuild without re-fetching API data

Use this if you want to rebuild database/tables/charts while keeping raw JSON files:

```powershell
Remove-Item data\processed\*.sqlite -Force -ErrorAction SilentlyContinue
Remove-Item reports\tables\*.csv -Force -ErrorAction SilentlyContinue
Remove-Item reports\figures\*.png -Force -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe main.py --skip-fetch
.\.venv\Scripts\python.exe check_db.py
```

---

## 13. What to commit to GitHub

Commit project code, documentation, and placeholder folders:

```text
README.md
main.py
check_db.py
requirements.txt
.gitignore
LICENSE
sql/
src/
docs/
docs/assets/successful_run.png
docs/assets/check_db_output.png
docs/assets/sample_chart.png
data/raw/.gitkeep
data/processed/.gitkeep
reports/figures/.gitkeep
reports/tables/.gitkeep
```

Do not commit generated raw JSON, generated SQLite database files, generated CSV exports, or generated chart files unless you intentionally want to include small sample outputs for portfolio display.

---

## 14. Troubleshooting

### PowerShell blocks activation

Use this instead:

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --country Singapore
```

### `ModuleNotFoundError`

Dependencies are missing from the virtual environment. Reinstall them:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### No data returned for an endpoint

Some OpenF1 endpoints are not populated for every session or weekend. This is expected. The pipeline should keep running where possible and use documented fallbacks.

### Starting grid data is missing

The pipeline may fall back to qualifying position as the grid proxy and mark the row with `grid_source = qualifying_result_fallback`.

### Charts do not appear

Check that the table files exist first:

```powershell
Get-ChildItem reports\tables
Get-ChildItem reports\figures
```

Then rerun:

```powershell
.\.venv\Scripts\python.exe main.py --skip-fetch
```

### Database looks stale

Reset generated files and rerun the pipeline:

```powershell
Remove-Item data\processed\*.sqlite -Force -ErrorAction SilentlyContinue
Remove-Item reports\tables\*.csv -Force -ErrorAction SilentlyContinue
Remove-Item reports\figures\*.png -Force -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe main.py --skip-fetch
.\.venv\Scripts\python.exe check_db.py
```

---

## 15. Replit notes

Upload the full project folder or connect the GitHub repository. In the Replit Shell:

```bash
python -m pip install -r requirements.txt
python main.py --year 2024 --country Singapore
python check_db.py
```

Replit does not need the Windows PowerShell activation command.

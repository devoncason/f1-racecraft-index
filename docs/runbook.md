# F1 Racecraft Index Runbook

This file is the practical step-by-step guide for running the project locally, in VS Code, or in Replit.

## 1. Open the project folder

Open the folder named `f1-racecraft-index`. The folder should contain:

```text
README.md
main.py
check_db.py
requirements.txt
src/
sql/
data/
reports/
```

## 2. Create and activate the virtual environment

```powershell
python -m venv .venv
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& ".\.venv\Scripts\Activate.ps1")
```

If activation is blocked, do not fight PowerShell. Use this pattern instead:

```powershell
.\.venv\Scripts\python.exe main.py --year 2024 --country Singapore
```

## 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Run a single race weekend

Use whatever year and country you want:

```powershell
python main.py --year 2024 --country Singapore
```

For a country with multiple races in the same year, include the meeting name:

```powershell
python main.py --year 2024 --country United States --meeting-name Miami
```

## 5. Run several selected race weekends

```powershell
python main.py --year 2024 --countries "Bahrain,Saudi Arabia,Australia,Japan,Monaco,Canada"
```

## 6. Run a whole season

```powershell
python main.py --season 2024
```

For testing, limit the number of weekends:

```powershell
python main.py --season 2024 --max-weekends 3
```

## 7. Rebuild from raw data without calling the API again

```powershell
python main.py --skip-fetch
```

This reloads the JSON files already saved in `data/raw/`, rebuilds the SQLite database, rebuilds the combined feature table, updates summary CSV files, and regenerates charts.

## 8. Check outputs

Important outputs:

```text
data/processed/f1_racecraft.sqlite
reports/tables/race_driver_features.csv
reports/tables/driver_context_summary.csv
reports/figures/
```

## 9. Verify with check_db.py

After a successful run:

```powershell
.\.venv\Scripts\python.exe check_db.py
```


## 10. GitHub upload notes

Do commit:

```text
README.md
main.py
check_db.py
requirements.txt
.gitignore
sql/
src/
docs/
data/raw/.gitkeep
data/processed/.gitkeep
reports/figures/.gitkeep
reports/tables/.gitkeep
```

Do not commit generated raw JSON, SQLite database files, PNG charts, or CSV report outputs unless you intentionally want to show sample outputs.

## 11. Replit notes

Upload the full project folder or connect the GitHub repository. In Replit Shell:

```bash
python -m pip install -r requirements.txt
python main.py --year 2024 --country Singapore
```

Replit does not need the Windows PowerShell activation command.

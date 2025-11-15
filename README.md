# nba_predictor_vscode

Minimal starter project for NBA prediction experiments.

Structure:

- `src/`: package with `data_collector.py` and `analyzer.py`.
- `notebooks/`: example Jupyter notebook `nba_analysis.ipynb`.
- `data/`: place to store CSVs or cached API data.
- `tests/`: test suite.

Quick start:

1. Create a virtual environment and install dependencies:

```
python -m venv .venv
.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. Open `notebooks/nba_analysis.ipynb` and run the cells.

Usage (CLI):

Run the single-match analyzer from the repository root using the project's virtual environment:

```powershell
.venv\Scripts\python.exe analyze_one.py --home "New York Knicks" --away "Miami Heat" --home-odds 1.53 --away-odds 4.5
```

Run tests locally:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

CI: this project includes a GitHub Actions workflow that runs `pytest` on push and pull requests (file: `.github/workflows/ci.yml`).

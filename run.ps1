param(
    [string]$Action = "help",
    [string[]]$Args = @()
)

# Helper script for local dev: run.ps1
# Usage:
#   .\run.ps1 -Action test
#   .\run.ps1 -Action app
#   .\run.ps1 -Action analyze -Args "--home","'New York Knicks'","--away","'Miami Heat'"

$venv = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$reports = Join-Path $PSScriptRoot "reports"
if (-not (Test-Path $reports)) { New-Item -ItemType Directory -Path $reports | Out-Null }

switch ($Action.ToLower()) {
    'test' {
        Write-Host "Running pytest and saving output to reports/pytest_output.txt..."
        & $venv -m pytest -vv 2>&1 | Tee-Object -FilePath (Join-Path $reports 'pytest_output.txt')
    }
    'app' {
        Write-Host "Starting Streamlit app (open browser to the printed URL)..."
        & $venv -m streamlit run app.py
    }
    'analyze' {
        if ($Args.Count -eq 0) {
            Write-Host "Example: .\run.ps1 -Action analyze -Args '--home','New York Knicks','--away','Miami Heat'"
        } else {
            Write-Host "Running analyze_one.py with args: $Args"
            & $venv (Join-Path $PSScriptRoot 'analyze_one.py') @Args
        }
    }
    default {
        Write-Host "run.ps1 helper"
        Write-Host "Actions: test, app, analyze"
        Write-Host "Examples:"
        Write-Host "  .\run.ps1 -Action test"
        Write-Host "  .\run.ps1 -Action app"
        Write-Host "  .\run.ps1 -Action analyze -Args '--home','New York Knicks','--away','Miami Heat'"
    }
}

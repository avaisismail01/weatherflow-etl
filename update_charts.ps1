# Regenerates the charts from the latest data and publishes them to GitHub.
# Usage (from the project folder):  powershell -ExecutionPolicy Bypass -File .\update_charts.ps1

Set-Location $PSScriptRoot

& .\venv\Scripts\python.exe charts.py
if ($LASTEXITCODE -ne 0) { Write-Host "Chart generation failed." -ForegroundColor Red; exit 1 }

git add docs/images
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { Write-Host "Charts unchanged, nothing to publish."; exit 0 }

git commit -m "Update charts with latest weather data"
git push
Write-Host "Charts updated on GitHub." -ForegroundColor Green

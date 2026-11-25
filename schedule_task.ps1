# Registers a Windows scheduled task that runs the WeatherFlow ETL pipeline every hour.
# Usage (from the project folder):  powershell -ExecutionPolicy Bypass -File .\schedule_task.ps1
# Remove it later with:             Unregister-ScheduledTask -TaskName WeatherFlowETL -Confirm:$false

$ProjectDir = $PSScriptRoot
$Python     = Join-Path $ProjectDir "venv\Scripts\pythonw.exe"   # pythonw = no console window
$Script     = Join-Path $ProjectDir "pipeline.py"

$Action  = New-ScheduledTaskAction -Execute $Python -Argument "`"$Script`"" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours((Get-Date).Hour + 1) `
           -RepetitionInterval (New-TimeSpan -Hours 1)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
            -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName "WeatherFlowETL" -Description "Hourly WeatherFlow ETL run" `
    -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null

Write-Host "Scheduled task 'WeatherFlowETL' registered: runs every hour on the hour."

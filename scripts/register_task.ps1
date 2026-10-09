# Registers a Windows Task Scheduler task that runs the pipeline once a day.
#
# Usage (from any folder):
#   powershell -ExecutionPolicy Bypass -File scripts\register_task.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\register_task.ps1 -At "07:30"
#
# Safe to run again: it replaces the existing task with the same name.
# To remove the task:  Unregister-ScheduledTask -TaskName WeatherETLPipeline

param(
    [string]$TaskName = "WeatherETLPipeline",
    [string]$At = "09:00"  # local time
)

$ErrorActionPreference = "Stop"

# Work out the project root from this script's location, not a hard-coded path.
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "venv not found at $Python. Create it first: python -m venv venv"
}

$action = New-ScheduledTaskAction -Execute $Python -Argument "-m src.pipeline" -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $At

# Laptop-friendly: run on battery, catch up a missed run, never run longer than 30 minutes.
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Description "Daily weather ETL: OpenWeatherMap -> PostgreSQL" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Force | Out-Null

$info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "Registered '$TaskName' to run daily at $At. Next run: $($info.NextRunTime)"

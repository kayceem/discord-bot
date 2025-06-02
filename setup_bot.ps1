$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPath = Join-Path $ProjectDir "venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$BotPath = Join-Path $ProjectDir "main.py"
$WebHookPath = Join-Path $ProjectDir "web_hook.py"
$Requirements = Join-Path $ProjectDir "requirements.txt"
$EnvExamplePath = Join-Path $ProjectDir ".env_example"
$EnvPath = Join-Path $ProjectDir ".env"
$TaskName = "DiscordScheduler"

if (!(Test-Path $VenvPath)) {
    Write-Host "Virtual environment not found. Creating venv..."
    python -m venv $VenvPath
    if (!(Test-Path $PythonExe)) {
        Write-Error "Failed to create virtual environment."
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists."
}

Write-Host "Installing dependencies from requirements.txt..."
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r $Requirements
Write-Host "`nDependencies installed successfully.`n"

if (!(Test-Path $EnvPath) -and (Test-Path $EnvExamplePath)) {
    Copy-Item $EnvExamplePath $EnvPath
    Write-Host "Copied .env_example to .env`n"
}

Write-Host "`nWhich script do you want to schedule?"
Write-Host "1. Discord Bot (main.py)"
Write-Host "2. Discord Webhook  (web_hook.py)"
$choice = Read-Host "Enter 1 or 2"

switch ($choice) {
    '1' {
        $ScriptPath = $BotPath
    }
    '2' {
        $ScriptPath = $WebHookPath
    }
    default {
        $ScriptPath = $BotPath
    }
}

if (!(Test-Path $ScriptPath)) {
    Write-Error "Selected script does not exist: $ScriptPath"
    exit 1
}

$addToScheduler = Read-Host "`nDo you want to schedule this script to run daily via Task Scheduler? (y/n)"

if ($addToScheduler -notmatch '^[Yy]$') {
    Write-Host "`nSetup completed. Skipping Task Scheduler configuration."
    exit 0
}

$ScheduledTime = Read-Host "`nEnter the time to run the bot daily (24-hour format, e.g., 14:00)"

if (-not ($ScheduledTime -match '^\d{1,2}:\d{2}$')) {
    Write-Error "Invalid time format. Use HH:mm (24-hour)."
    exit
}

$TimeParts = $ScheduledTime -split ':'
$ScheduledHour = [int]$TimeParts[0]
$ScheduledMinute = [int]$TimeParts[1]

$StartBoundary = [datetime]::Today.AddHours($ScheduledHour).AddMinutes($ScheduledMinute).ToString("s")

$TaskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>$StartBoundary</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>SYSTEM</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>StopExisting</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$PythonExe</Command>
      <Arguments>"$ScriptPath"</Arguments>
      <WorkingDirectory>$ProjectDir</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

$TaskFile = "$env:TEMP\DiscordSchedulerTask.xml"
$TaskXml | Out-File -Encoding Unicode $TaskFile

schtasks.exe /Create /TN "$TaskName" /XML "$TaskFile" /F

Remove-Item "$TaskFile"
Write-Host "Scheduled task '$TaskName' created with 'Stop existing instance' rule."

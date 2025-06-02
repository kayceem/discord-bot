$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExePath = Join-Path $ProjectDir "discord_scheduler_bot.exe"
$TaskName = "DiscordSchedulerBot"

if (!(Test-Path $ExePath)) {
    Write-Host "Executable not found. Please ensure the bot is compiled to an executable."
    exit 1
}

$ScheduledTime = Read-Host "Enter the time to run the bot daily (24-hour format, e.g., 14:00)"

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
      <Command>$ExePath</Command>
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

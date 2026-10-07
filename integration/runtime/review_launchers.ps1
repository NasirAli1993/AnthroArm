$ErrorActionPreference = 'Stop'
. 'D:\RoboticArm\scripts\environment.ps1'
$reviewFiles = @('D:\RoboticArm\START_SIMULATION.ps1','D:\RoboticArm\STOP_SIMULATION.ps1','D:\RoboticArm\RUN_VALIDATION.ps1','D:\RoboticArm\integration\navigation\launch.ps1','D:\RoboticArm\integration\runtime\run_ros2.ps1')
$reviewChecks = @()
foreach ($reviewFile in $reviewFiles) {
    $reviewTokens = $null
    $reviewErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($reviewFile, [ref]$reviewTokens, [ref]$reviewErrors) | Out-Null
    $reviewChecks += @{ path=$reviewFile; passed=($reviewErrors.Count -eq 0); errors=@($reviewErrors | ForEach-Object { $_.Message }) }
}
$reviewReport = @{ passed=(@($reviewChecks | Where-Object { !$_.passed }).Count -eq 0); powershell_version=$PSVersionTable.PSVersion.ToString(); checks=$reviewChecks; scope='Parse-only under system Windows PowerShell; no service or browser launched' }
$reviewReport | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath 'D:\RoboticArm\results\integration\runtime\review_launcher_checks.json' -Encoding UTF8
$reviewReport | ConvertTo-Json -Depth 6
if (!$reviewReport.passed) { exit 1 }

param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
. 'D:\RoboticArm\scripts\environment.ps1'
$simulationRoot = 'D:\RoboticArm'
$simulationLogs = "$simulationRoot\results\integration"
$simulationShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$simulationProcesses = Get-CimInstance Win32_Process -Filter "name='python.exe'"
$runtimeUp = $false
try { $h = Invoke-RestMethod 'http://127.0.0.1:8770/health' -TimeoutSec 2; $runtimeUp = [bool]$h.ready -and !$h.error } catch {}
if (!$runtimeUp) {
    $existing = $simulationProcesses | Where-Object { $_.CommandLine -match 'integration[\\/]runtime_server.py' }
    if (!$existing) {
        Start-Process "$simulationRoot\software\python\python.exe" -ArgumentList "$simulationRoot\integration\runtime_server.py" -WorkingDirectory $simulationRoot -WindowStyle Hidden -RedirectStandardOutput "$simulationLogs\runtime_server.log" -RedirectStandardError "$simulationLogs\runtime_server_error.log" | Out-Null
    }
    $deadline = (Get-Date).AddSeconds(60)
    do {
        Start-Sleep -Milliseconds 500
        try { $h=Invoke-RestMethod 'http://127.0.0.1:8770/health' -TimeoutSec 2; $runtimeUp=[bool]$h.ready -and !$h.error } catch {}
    } until ($runtimeUp -or (Get-Date) -gt $deadline)
    if (!$runtimeUp) { throw 'Arm runtime failed to start. See results\integration\runtime_server_error.log.' }
}
if (!($simulationProcesses | Where-Object { $_.CommandLine -match 'integration[\\/]ros2[\\/]anthro_bridge.py' })) {
    Start-Process $simulationShell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"$simulationRoot\integration\runtime\run_ros2.ps1",'python',"$simulationRoot\integration\ros2\anthro_bridge.py") -WorkingDirectory $simulationRoot -WindowStyle Hidden -RedirectStandardOutput "$simulationLogs\arm_ros.log" -RedirectStandardError "$simulationLogs\arm_ros_error.log" | Out-Null
}
& "$simulationRoot\integration\navigation\launch.ps1"
Write-Output 'Simulation studio: http://127.0.0.1:8770'
Write-Output 'All interfaces are simulation-only and bound to this computer.'
if (!$NoBrowser) {
    $simulationBrowser = @('C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe','C:\Program Files\Google\Chrome\Application\chrome.exe') | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($simulationBrowser) {
        Start-Process -FilePath $simulationBrowser -ArgumentList '--user-data-dir=D:\RoboticArm\profile\browser','--disk-cache-dir=D:\RoboticArm\cache\browser','--no-first-run','--app=http://127.0.0.1:8770'
    } else { Write-Output 'Open http://127.0.0.1:8770 in your browser.' }
}

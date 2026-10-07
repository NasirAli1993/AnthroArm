$ErrorActionPreference = 'Stop'
foreach ($simulationPort in @(8770,8771)) {
    try { Invoke-RestMethod "http://127.0.0.1:$simulationPort/command" -Method Post -ContentType 'application/json' -Body '{"op":"stop"}' -TimeoutSec 3 | Out-Null } catch {}
}
$simulationProcesses=Get-CimInstance Win32_Process -Filter "name='python.exe'"
$simulationPatterns=@('D:\RoboticArm\integration\runtime_server.py','D:\RoboticArm\integration\ros2\anthro_bridge.py','D:\RoboticArm\integration\navigation\backend.py','D:\RoboticArm\integration\navigation\ros_bridge.py')
foreach ($simulationProcess in $simulationProcesses) {
    $normalizedCommand=$simulationProcess.CommandLine -replace '/','\'
    foreach ($simulationPattern in $simulationPatterns) {
        if ($normalizedCommand -like "*$simulationPattern*") { Stop-Process -Id $simulationProcess.ProcessId; break }
    }
}
Write-Output 'Stopped only the four integrated simulation services.'

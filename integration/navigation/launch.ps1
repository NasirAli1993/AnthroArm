$ErrorActionPreference = 'Stop'
. 'D:\RoboticArm\scripts\environment.ps1'
$navigationRoot = 'D:\RoboticArm\integration\navigation'
$navigationResults = 'D:\RoboticArm\results\integration\navigation'
$backendReady = $false
try { $backendState = Invoke-RestMethod -Uri 'http://127.0.0.1:8771/state' -TimeoutSec 2; $backendReady = [bool]$backendState.ready } catch {}
if (!$backendReady) {
    $existingBackend = Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -like '*integration\navigation\backend.py*' }
    if (!$existingBackend) {
        Start-Process -FilePath 'D:\RoboticArm\software\python\python.exe' -ArgumentList @('-u',"$navigationRoot\backend.py",'--speed','3') -WorkingDirectory 'D:\RoboticArm' -WindowStyle Hidden -RedirectStandardOutput "$navigationResults\backend.log" -RedirectStandardError "$navigationResults\backend.err" | Out-Null
    }
}
$existingBridge = Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -like '*integration\navigation\ros_bridge.py*' }
if (!$existingBridge) {
    Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','D:\RoboticArm\integration\runtime\run_ros2.ps1','python',"$navigationRoot\ros_bridge.py") -WorkingDirectory 'D:\RoboticArm' -WindowStyle Hidden -RedirectStandardOutput "$navigationResults\ros_bridge.log" -RedirectStandardError "$navigationResults\ros_bridge.err" | Out-Null
}
Write-Output 'Navigation simulation: http://127.0.0.1:8771/state'
Write-Output 'Actual physics image: http://127.0.0.1:8771/frame.jpg'
Write-Output 'ROS service /mobile/run_mission starts the mapping/navigation mission.'

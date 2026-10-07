. 'D:\RoboticArm\scripts\environment.ps1'
try {
    Invoke-RestMethod -Uri 'http://127.0.0.1:8765/command' -Method Post -ContentType 'application/json' -Body '{"action":"teleop","value":true}' | Out-Null
} catch {
    Write-Host 'Start Robotics Studio first, then run Webcam Control again.'
    Read-Host 'Press Enter to close'
    exit 1
}
try {
    & 'D:\RoboticArm\software\python\python.exe' 'D:\RoboticArm\simulation\webcam_teleop.py'
} finally {
    try { Invoke-RestMethod -Uri 'http://127.0.0.1:8765/command' -Method Post -ContentType 'application/json' -Body '{"action":"teleop","value":false}' | Out-Null } catch { }
}

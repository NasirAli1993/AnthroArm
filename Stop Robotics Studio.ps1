$taskPidPath = 'D:\RoboticArm\results\server.pid'
if (Test-Path -LiteralPath $taskPidPath) {
    $taskServerPid = [int](Get-Content -LiteralPath $taskPidPath -Raw)
    $taskServerProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$taskServerPid" -ErrorAction SilentlyContinue
    if ($taskServerProcess -and $taskServerProcess.CommandLine -like '*D:\RoboticArm\simulation\server.py*') {
        Stop-Process -Id $taskServerPid
    }
}

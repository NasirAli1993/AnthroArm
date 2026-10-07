foreach ($taskService in @(@{Pid='results\server.pid';Script='D:\RoboticArm\simulation\server.py'},@{Pid='results\v3\server.pid';Script='D:\RoboticArm\simulation\v3\server.py'})) {
    $taskPidPath = "D:\RoboticArm\$($taskService.Pid)"
    if (Test-Path -LiteralPath $taskPidPath) {
        $taskServerPid = [int](Get-Content -LiteralPath $taskPidPath -Raw)
        $taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$taskServerPid" -ErrorAction SilentlyContinue
        if ($taskProcess -and $taskProcess.CommandLine.Contains($taskService.Script)) { Stop-Process -Id $taskServerPid }
    }
}

param([ValidateSet('presentation','live','vision')][string]$View = 'presentation', [switch]$NoBrowser)
. 'D:\RoboticArm\scripts\environment.ps1'
foreach ($taskService in @(@{Port=8765;Script='simulation\server.py';Log='results'},@{Port=8766;Script='simulation\v3\server.py';Log='results\v3'})) {
    $taskListener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $taskService.Port -State Listen -ErrorAction SilentlyContinue
    if (-not $taskListener) {
        Start-Process -FilePath 'D:\RoboticArm\software\python\python.exe' -ArgumentList "D:\RoboticArm\$($taskService.Script)" -WorkingDirectory 'D:\RoboticArm' -WindowStyle Hidden -RedirectStandardOutput "D:\RoboticArm\$($taskService.Log)\studio.log" -RedirectStandardError "D:\RoboticArm\$($taskService.Log)\studio_error.log"
    }
}
$taskUrl = switch ($View) { 'live' {'http://127.0.0.1:8766/'} 'vision' {'http://127.0.0.1:8766/?mode=vision'} default {'http://127.0.0.1:8765/presentation'} }
if (-not $NoBrowser) {
    $taskBrowser = @('C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe','C:\Program Files\Google\Chrome\Application\chrome.exe') | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($taskBrowser) {
        Start-Process -FilePath $taskBrowser -ArgumentList '--user-data-dir=D:\RoboticArm\profile\browser','--disk-cache-dir=D:\RoboticArm\cache\browser','--no-first-run',"--app=$taskUrl"
    } else { Write-Host "Open $taskUrl in your browser." }
}

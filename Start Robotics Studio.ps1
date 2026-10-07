param([ValidateSet('/','/design')][string]$View = '/')
. 'D:\RoboticArm\scripts\environment.ps1'
$running = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if (-not $running) {
    Start-Process -FilePath 'D:\RoboticArm\software\python\python.exe' -ArgumentList 'D:\RoboticArm\simulation\server.py' -WorkingDirectory 'D:\RoboticArm' -WindowStyle Hidden -RedirectStandardOutput 'D:\RoboticArm\results\studio.log' -RedirectStandardError 'D:\RoboticArm\results\studio_error.log'
}
$taskBrowser = @('C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe','C:\Program Files\Google\Chrome\Application\chrome.exe') | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ($taskBrowser) {
    Start-Process -FilePath $taskBrowser -ArgumentList '--user-data-dir=D:\RoboticArm\profile\browser','--disk-cache-dir=D:\RoboticArm\cache\browser','--no-first-run',"--app=http://127.0.0.1:8765$View"
} else {
    Write-Host 'Studio is running. Open http://127.0.0.1:8765 in your browser.'
}

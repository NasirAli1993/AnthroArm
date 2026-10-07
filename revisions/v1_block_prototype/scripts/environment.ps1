$ErrorActionPreference = 'Stop'
$taskRoot = 'D:\RoboticArm'
$env:TEMP = "$taskRoot\temp"
$env:TMP = "$taskRoot\temp"
$env:USERPROFILE = "$taskRoot\profile"
$env:APPDATA = "$taskRoot\profile\AppData\Roaming"
$env:LOCALAPPDATA = "$taskRoot\profile\AppData\Local"
$env:XDG_CACHE_HOME = "$taskRoot\cache"
$env:PIP_CACHE_DIR = "$taskRoot\cache\pip"
$env:MPLCONFIGDIR = "$taskRoot\cache\matplotlib"
$env:HF_HOME = "$taskRoot\cache\huggingface"
$env:TORCH_HOME = "$taskRoot\cache\torch"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONNOUSERSITE = '1'
New-Item -ItemType Directory -Force -Path $env:TEMP,$env:APPDATA,$env:LOCALAPPDATA,$env:MPLCONFIGDIR | Out-Null
Set-Location -LiteralPath $taskRoot

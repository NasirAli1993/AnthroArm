param([string]$source,[string]$target,[string]$payloadFile)
$ErrorActionPreference='Stop'
function Literal([string]$s){return "'"+$s.Replace("'","''")+"'"}
$payload=((Get-Content -LiteralPath $payloadFile | Select-Object -Skip 1) -join ' ')
$text='$source='+(Literal $source)+'; $target='+(Literal $target)+'; '+$payload
$exe=$env:SystemRoot+'\System32\WindowsPowerShell\v1.0\powershell.exe'
$command='"'+$exe+'" -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -Command "'+$text+'"'
$shell=New-Object -ComObject WScript.Shell
$code=$shell.Run($command,0,$true)
Write-Output $code
exit $code

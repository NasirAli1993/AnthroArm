$ErrorActionPreference = 'Stop'
. 'D:\RoboticArm\scripts\environment.ps1'
& 'D:\RoboticArm\software\python\python.exe' 'D:\RoboticArm\integration\test_runtime.py'
if ($LASTEXITCODE -ne 0) { throw 'Runtime validation failed' }
Write-Output 'Runtime test complete. Independent grasp and navigation test commands are in their README.txt files.'

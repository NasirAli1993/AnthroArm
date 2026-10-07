$ErrorActionPreference = 'Stop'
. 'D:\RoboticArm\scripts\environment.ps1'
$env:FREECAD_USER_HOME = 'D:\RoboticArm\profile\FreeCAD'
$cadCmd = Get-ChildItem -LiteralPath 'D:\RoboticArm\software\freecad' -Recurse -Filter FreeCADCmd.exe | Select-Object -First 1 -ExpandProperty FullName
$reportPath = 'D:\RoboticArm\results\cad_validation.json'
if (Test-Path -LiteralPath $reportPath) { Remove-Item -LiteralPath $reportPath }
& $cadCmd -u 'D:\RoboticArm\profile\FreeCAD\validation_user.cfg' -s 'D:\RoboticArm\profile\FreeCAD\validation_system.cfg' 'D:\RoboticArm\design\validate_cad.py'
if ($LASTEXITCODE -ne 0) { throw 'FreeCAD validation process failed.' }
if (!(Test-Path -LiteralPath $reportPath)) { throw 'CAD validation did not produce a report.' }
$cadReport = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
if (!$cadReport.passed) { throw 'CAD round-trip validation failed. See results/cad_validation.json.' }

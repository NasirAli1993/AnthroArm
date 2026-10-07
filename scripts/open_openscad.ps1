$ErrorActionPreference = 'Stop'
. 'D:\RoboticArm\scripts\environment.ps1'
$scadExe = Get-ChildItem -LiteralPath 'D:\RoboticArm\software\openscad' -Recurse -Filter openscad.exe | Select-Object -First 1 -ExpandProperty FullName
$scadDocument = 'D:\RoboticArm\design\humanoid_hand.scad'
if (!(Test-Path -LiteralPath $scadDocument)) { $scadDocument = 'D:\RoboticArm\design\arm_hand.scad' }
& $scadExe $scadDocument

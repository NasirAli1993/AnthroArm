$ErrorActionPreference = 'Stop'
. 'D:\RoboticArm\scripts\environment.ps1'
$env:FREECAD_USER_HOME = 'D:\RoboticArm\profile\FreeCAD'
$cadExe = Get-ChildItem -LiteralPath 'D:\RoboticArm\software\freecad' -Recurse -Filter FreeCAD.exe | Select-Object -First 1 -ExpandProperty FullName
if (!$cadExe) { throw 'Portable FreeCAD executable is not present.' }
& $cadExe -u 'D:\RoboticArm\profile\FreeCAD\user.cfg' -s 'D:\RoboticArm\profile\FreeCAD\system.cfg' 'D:\RoboticArm\design\AnthroArm25.FCStd'

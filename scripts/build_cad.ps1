$ErrorActionPreference = 'Stop'
. 'D:\RoboticArm\scripts\environment.ps1'
$env:FREECAD_USER_HOME = 'D:\RoboticArm\profile\FreeCAD'
New-Item -ItemType Directory -Force -Path $env:FREECAD_USER_HOME | Out-Null
$cadExe = Get-ChildItem -LiteralPath 'D:\RoboticArm\software\freecad' -Recurse -Filter FreeCAD.exe | Select-Object -First 1 -ExpandProperty FullName
if (!$cadExe) { throw 'Portable FreeCAD executable is not present.' }
& 'D:\RoboticArm\software\python\python.exe' 'D:\RoboticArm\design\generate_scad_parameters.py'
& $cadExe -u 'D:\RoboticArm\profile\FreeCAD\anatomical_user.cfg' -s 'D:\RoboticArm\profile\FreeCAD\anatomical_system.cfg' 'D:\RoboticArm\design\build_anatomical_cad.FCMacro'

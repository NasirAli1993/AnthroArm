$ErrorActionPreference = 'Stop'
. 'D:\RoboticArm\scripts\environment.ps1'
$env:FREECAD_USER_HOME = 'D:\RoboticArm\profile\FreeCAD'
$cadCmd = 'D:\RoboticArm\software\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\FreeCADCmd.exe'
& $cadCmd -u 'D:\RoboticArm\profile\FreeCAD\v3_validate.cfg' -s 'D:\RoboticArm\profile\FreeCAD\v3_validate_system.cfg' 'D:\RoboticArm\design\v3\validate_reference_arm.py'
if ($LASTEXITCODE -ne 0) { throw 'V3 full-arm validation failed to execute.' }
$armReport = Get-Content -Raw -LiteralPath 'D:\RoboticArm\results\v3\anatomical_cad_validation.json' | ConvertFrom-Json
if (!$armReport.passed) { throw 'V3 full-arm geometry validation failed.' }
& $cadCmd -u 'D:\RoboticArm\profile\FreeCAD\v3_finger_validate.cfg' -s 'D:\RoboticArm\profile\FreeCAD\v3_finger_validate_system.cfg' 'D:\RoboticArm\design\v3\validate_printable_finger.py'
if ($LASTEXITCODE -ne 0) { throw 'Finger prototype validation failed to execute.' }
$fingerReport = Get-Content -Raw -LiteralPath 'D:\RoboticArm\results\v3\printable_finger_validation.json' | ConvertFrom-Json
if (!$fingerReport.topology_passed -or !$fingerReport.no_hard_intersections_in_checked_poses) { throw 'Finger prototype geometry/clearance validation failed.' }
Write-Output 'V3 full-arm and finger prototype geometry checks passed. This does not validate physical fabrication or powered operation.'

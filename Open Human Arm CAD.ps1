. 'D:\RoboticArm\scripts\environment.ps1'
$env:FREECAD_USER_HOME = 'D:\RoboticArm\profile\FreeCAD'
Start-Process -FilePath 'D:\RoboticArm\software\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecad.exe' -ArgumentList '-u','D:\RoboticArm\profile\FreeCAD\user.cfg','-s','D:\RoboticArm\profile\FreeCAD\system.cfg','D:\RoboticArm\design\v3\AnthroArm27_ReferenceV3.FCStd','D:\RoboticArm\design\v3\printable_finger\TendonFinger_FitTest.FCStd' -WorkingDirectory 'D:\RoboticArm'

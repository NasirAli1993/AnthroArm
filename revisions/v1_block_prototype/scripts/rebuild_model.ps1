. 'D:\RoboticArm\scripts\environment.ps1'
& 'D:\RoboticArm\software\python\python.exe' 'D:\RoboticArm\scripts\rebuild_model.py'
if ($LASTEXITCODE -ne 0) { throw 'Robot model regeneration failed.' }

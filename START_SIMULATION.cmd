@echo off
cd /d D:\RoboticArm
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "D:\RoboticArm\START_SIMULATION.ps1"
if errorlevel 1 pause

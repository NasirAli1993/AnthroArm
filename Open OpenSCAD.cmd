@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ". 'D:\RoboticArm\scripts\environment.ps1'; & 'D:\RoboticArm\software\openscad\openscad-2021.01\openscad.exe' 'D:\RoboticArm\design\arm_hand.scad'"

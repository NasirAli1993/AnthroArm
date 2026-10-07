# Usage: & 'D:\RoboticArm\integration\runtime\run_ros2.ps1' python path\node.py
# Or:    & 'D:\RoboticArm\integration\runtime\run_ros2.ps1' ros2 topic list
. 'D:\RoboticArm\integration\runtime\environment.ps1'
$runtimeCommand = @($args)
if ($runtimeCommand.Count -eq 0) { $runtimeCommand = @('ros2', '--help') }
& 'D:\RoboticArm\software\ros2\pixi.exe' run --manifest-path 'D:\RoboticArm\software\ros2\pixi.toml' @runtimeCommand
exit $LASTEXITCODE

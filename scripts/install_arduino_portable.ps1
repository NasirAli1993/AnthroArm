$ErrorActionPreference = 'Stop'
. 'D:\RoboticArm\scripts\environment.ps1'
$taskArduino = 'D:\RoboticArm\software\arduino-cli'
New-Item -ItemType Directory -Force -Path $taskArduino,'D:\RoboticArm\software\arduino-data','D:\RoboticArm\downloads\arduino','D:\RoboticArm\hardware\libraries','D:\RoboticArm\cache\arduino','D:\RoboticArm\hardware\single_finger' | Out-Null
$taskRelease = Invoke-RestMethod -Uri 'https://api.github.com/repos/arduino/arduino-cli/releases/latest'
$taskZip = $taskRelease.assets | Where-Object name -Match 'Windows_64bit.zip$' | Select-Object -First 1
if (!$taskZip) { throw 'Official Windows x64 release asset missing' }
$taskArchive = Join-Path 'D:\RoboticArm\downloads\arduino' $taskZip.name
Invoke-WebRequest -Uri $taskZip.browser_download_url -OutFile $taskArchive
$taskChecksums = $taskRelease.assets | Where-Object name -Match 'checksums.txt$' | Select-Object -First 1
if ($taskChecksums) {
    $taskChecksumPath = 'D:\RoboticArm\downloads\arduino\checksums.txt'
    Invoke-WebRequest -Uri $taskChecksums.browser_download_url -OutFile $taskChecksumPath
    $taskHashLine = Get-Content -LiteralPath $taskChecksumPath | Where-Object { $_ -like "*$($taskZip.name)" } | Select-Object -First 1
    $taskExpectedHash = ($taskHashLine -split '\s+')[0]
    if ((Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLower() -ne $taskExpectedHash.ToLower()) { throw 'Official archive hash mismatch' }
}
Expand-Archive -LiteralPath $taskArchive -DestinationPath $taskArduino -Force
$taskConfig = 'D:\RoboticArm\software\arduino-cli\arduino-cli.yaml'
@'
directories:
  data: D:/RoboticArm/software/arduino-data
  downloads: D:/RoboticArm/downloads/arduino/packages
  user: D:/RoboticArm/hardware
build_cache:
  path: D:/RoboticArm/cache/arduino
updater:
  enable_notification: false
'@ | Set-Content -LiteralPath $taskConfig -Encoding utf8
@{version=$taskRelease.tag_name;source=$taskZip.browser_download_url;sha256=(Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash;install=$taskArduino;config=$taskConfig} | ConvertTo-Json | Set-Content -LiteralPath 'D:\RoboticArm\results\v3\arduino_install.json'
& "$taskArduino\arduino-cli.exe" --config-file $taskConfig core update-index
if ($LASTEXITCODE -ne 0) { throw 'Arduino index update failed' }
& "$taskArduino\arduino-cli.exe" --config-file $taskConfig core install arduino:avr
if ($LASTEXITCODE -ne 0) { throw 'AVR core installation failed' }
& "$taskArduino\arduino-cli.exe" --config-file $taskConfig lib install Servo
if ($LASTEXITCODE -ne 0) { throw 'Servo library installation failed' }

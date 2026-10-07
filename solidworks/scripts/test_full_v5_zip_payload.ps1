param([string]$source,[string]$target)
$ErrorActionPreference='Stop'; $job=$null;
try {
  if(Test-Path -LiteralPath $target){throw 'Refusing an existing ZIP'};
  $job=Start-Job -ScriptBlock { param($source,$target)
    $ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';
    if(Test-Path -LiteralPath $target){throw 'Refusing an existing ZIP'};
    $files=@(Get-ChildItem -LiteralPath $source -File -Force);
    if($files.Count -ne 30){throw 'Expected exactly 28 native parts, one assembly and one log'};
    if(@($files|Where-Object {$_.Extension -ieq '.SLDPRT'}).Count -ne 28){throw 'Wrong native part file count'};
    if(@($files|Where-Object {$_.Name -ieq 'AnthroArm27_STATIC_HOME.SLDASM'}).Count -ne 1){throw 'Missing native assembly'};
    if(@($files|Where-Object {$_.Name -ieq 'Native_Static_Build.log'}).Count -ne 1){throw 'Missing build log'};
    foreach($file in $files){if($file.Length -le 0){throw 'Empty source file'}};
    Compress-Archive -LiteralPath $source -DestinationPath $target -CompressionLevel Optimal -ErrorAction Stop;
    Add-Type -AssemblyName System.IO.Compression.FileSystem;
    $zip=[System.IO.Compression.ZipFile]::OpenRead($target);
    try {
      $entries=@($zip.Entries|Where-Object {$_.Name.Length -gt 0});
      if($entries.Count -ne 30){throw 'ZIP file-entry count mismatch'};
      $prefix=(Split-Path -Leaf $source)+'/';
      foreach($file in $files){
        $match=@($entries|Where-Object {$_.FullName.Replace('\','/') -ceq ($prefix+$file.Name)});
        if($match.Count -ne 1){throw 'ZIP expected filename mismatch'};
        if($match[0].Length -ne $file.Length){throw 'ZIP entry length mismatch'};
        $stream=$match[0].Open(); try {$stream.CopyTo([System.IO.Stream]::Null)} finally {$stream.Dispose()};
      };
    } finally {$zip.Dispose()};
    if((Get-Item -LiteralPath $target).Length -le 0){throw 'ZIP is empty'};
  } -ArgumentList $source,$target;
  $done=Wait-Job -Job $job -Timeout 60;
  if($null -eq $done){Stop-Job -Job $job; Remove-Job -Job $job; exit 124};
  if($job.State -ne 'Completed'){Receive-Job -Job $job -ErrorAction Stop|Out-Null; throw 'ZIP job failed'};
  Receive-Job -Job $job -ErrorAction Stop|Out-Null; Remove-Job -Job $job; exit 0;
} catch { if($null -ne $job){Stop-Job -Job $job -ErrorAction SilentlyContinue; Remove-Job -Job $job -Force -ErrorAction SilentlyContinue}; exit 1 };
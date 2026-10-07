param([string]$source,[string]$target)
$ErrorActionPreference='Stop'; $job=$null; 
try { 
  if(Test-Path -LiteralPath $target){throw 'Refusing an existing ZIP'}; 
  $job=Start-Job -ScriptBlock { param($source,$target) 
    $ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; 
    if(Test-Path -LiteralPath $target){throw 'Refusing an existing ZIP'}; 
    $required=@('index_intermediate.SLDPRT','index_distal.SLDPRT','DIP_PLACEMENT_ONLY.SLDASM','DIP_HINGE_MATED.SLDASM','DIP_DRIVEN_10DEG.SLDASM','DIP_DRIVEN_RETURN_ZERO.SLDASM','DIP_LIMITED_0_TO_80DEG.SLDASM','Native_DIP_Mate.log','native_pose_measurements.csv'); 
    $files=@(foreach($name in $required){Get-Item -LiteralPath (Join-Path $source $name) -Force -ErrorAction Stop}); 
    if($files.Count -ne 9){throw 'Expected exactly nine named native deliverables'}; 
    foreach($file in $files){if($file.PSIsContainer){throw 'Deliverable is a directory'}}; 
    foreach($file in $files){if($file.Length -le 0){throw 'Empty source file'}}; 
    Compress-Archive -LiteralPath @($files.FullName) -DestinationPath $target -CompressionLevel Optimal -ErrorAction Stop; 
    Add-Type -AssemblyName System.IO.Compression.FileSystem; 
    $zip=[System.IO.Compression.ZipFile]::OpenRead($target); 
    try { 
      $entries=@($zip.Entries|Where-Object {$_.Name.Length -gt 0}); 
      if($entries.Count -ne 9){throw 'ZIP file-entry count mismatch'}; 
      foreach($file in $files){ 
        $match=@($entries|Where-Object {$_.FullName.Replace('\','/') -ceq $file.Name}); 
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

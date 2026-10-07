param([string]$source,[string]$target)
$ErrorActionPreference='Stop'; $job=$null; 
try { 
  if(Test-Path -LiteralPath $target){throw 'Refusing an existing ZIP'}; 
  $job=Start-Job -ScriptBlock { param($source,$target) 
    $ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; 
    if(Test-Path -LiteralPath $target){throw 'Refusing an existing ZIP'}; 
    $required=@('base_link.SLDPRT','shoulder_abduction.SLDPRT','shoulder_flexion.SLDPRT','upper_arm.SLDPRT','elbow_link.SLDPRT','forearm.SLDPRT','wrist_pitch.SLDPRT','palm_base.SLDPRT','index_knuckle.SLDPRT','index_proximal.SLDPRT','index_intermediate.SLDPRT','index_distal.SLDPRT','middle_knuckle.SLDPRT','middle_proximal.SLDPRT','middle_intermediate.SLDPRT','middle_distal.SLDPRT','ring_knuckle.SLDPRT','ring_proximal.SLDPRT','ring_intermediate.SLDPRT','ring_distal.SLDPRT','pinky_knuckle.SLDPRT','pinky_proximal.SLDPRT','pinky_intermediate.SLDPRT','pinky_distal.SLDPRT','thumb_opposition.SLDPRT','thumb_metacarpal.SLDPRT','thumb_proximal.SLDPRT','thumb_distal.SLDPRT','AnthroArm27_STATIC_HOME.SLDASM','Native_Static_Build.log'); 
    $files=@(foreach($name in $required){Get-Item -LiteralPath (Join-Path $source $name) -Force -ErrorAction Stop}); 
    if($files.Count -ne 30){throw 'Expected exactly 30 named native deliverables'}; 
    foreach($file in $files){if($file.PSIsContainer){throw 'Deliverable is a directory'}}; 
    foreach($file in $files){if($file.Length -le 0){throw 'Empty source file'}}; 
    Compress-Archive -LiteralPath @($files.FullName) -DestinationPath $target -CompressionLevel Optimal -ErrorAction Stop; 
    Add-Type -AssemblyName System.IO.Compression.FileSystem; 
    $zip=[System.IO.Compression.ZipFile]::OpenRead($target); 
    try { 
      $entries=@($zip.Entries|Where-Object {$_.Name.Length -gt 0}); 
      if($entries.Count -ne 30){throw 'ZIP file-entry count mismatch'}; 
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
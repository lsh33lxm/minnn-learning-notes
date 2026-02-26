Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 1
$soundDir = Join-Path $PSScriptRoot 'sounds'
if (-not (Test-Path $soundDir)) { New-Item -ItemType Directory -Path $soundDir | Out-Null }

$msgs = @{}
$msgs['prompt_submit'] = 'At your service, Minnn'
$msgs['need_confirm'] = 'Minnn, I need your confirmation'
$msgs['task_done'] = 'Task completed, Minnn'
$msgs['subagent_done'] = 'Sub agent has finished'
$msgs['pre_compact'] = 'Compacting context now'
$msgs['notification'] = 'Minnn, you have a new notification'

foreach ($key in $msgs.Keys) {
    $file = Join-Path $soundDir ($key + '.wav')
    Write-Output ('Generating: ' + $file)
    $synth.SetOutputToWaveFile($file)
    $synth.Speak($msgs[$key])
}

$synth.Dispose()
Write-Output 'All sound files generated successfully'

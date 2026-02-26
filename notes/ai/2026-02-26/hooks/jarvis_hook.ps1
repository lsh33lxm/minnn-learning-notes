$input_data = [Console]::In.ReadToEnd()
$soundDir = Join-Path $PSScriptRoot 'sounds'

try {
    $json = $input_data | ConvertFrom-Json
} catch {
    Write-Output '{}'
    exit 0
}

$event = $json.hook_event_name
$audioFile = $null

switch ($event) {
    'UserPromptSubmit' { $audioFile = 'prompt_submit.mp3' }
    'Notification' {
        if ($json.notification_type -eq 'permission_prompt') {
            $audioFile = 'need_confirm.mp3'
        } else {
            $audioFile = 'notification.mp3'
        }
    }
    'Stop' {
        if ($json.stop_hook_active -eq $true) {
            Write-Output '{}'
            exit 0
        }
        $audioFile = 'task_done.mp3'
    }
    'SubagentStop' { $audioFile = 'subagent_done.mp3' }
    'PreCompact'   { $audioFile = 'pre_compact.mp3' }
}

if ($audioFile) {
    $fullPath = Join-Path $soundDir $audioFile
    if (Test-Path $fullPath) {
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class WinMM {
    [DllImport("winmm.dll")]
    public static extern int mciSendString(string cmd, System.Text.StringBuilder ret, int retLen, IntPtr hwnd);
}
"@
        [WinMM]::mciSendString("open `"$fullPath`" type mpegvideo alias jarvis", $null, 0, [IntPtr]::Zero)
        [WinMM]::mciSendString("play jarvis wait", $null, 0, [IntPtr]::Zero)
        [WinMM]::mciSendString("close jarvis", $null, 0, [IntPtr]::Zero)
    }
}

Write-Output '{}'
exit 0

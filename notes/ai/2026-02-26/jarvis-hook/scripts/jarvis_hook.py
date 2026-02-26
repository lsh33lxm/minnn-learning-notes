"""
JARVIS Hook - 读取 stdin JSON，播放对应 mp3 语音。
使用 ctypes 直接调用 winmm.dll mciSendString（零依赖，无 PowerShell 开销）。
"""
import sys
import json
import os
import ctypes

winmm = ctypes.windll.winmm

def play(path):
    p = path.replace('"', '')
    winmm.mciSendStringW(f'open "{p}" type mpegvideo alias jv', None, 0, 0)
    winmm.mciSendStringW('play jv wait', None, 0, 0)
    winmm.mciSendStringW('close jv', None, 0, 0)

def main():
    sound_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        print('{}')
        return

    event = data.get('hook_event_name', '')
    f = None

    if event == 'UserPromptSubmit':
        f = 'prompt_submit.mp3'
    elif event == 'Notification':
        if data.get('notification_type') == 'permission_prompt':
            f = 'need_confirm.mp3'
        else:
            f = 'notification.mp3'
    elif event == 'Stop':
        if data.get('stop_hook_active'):
            print('{}')
            return
        f = 'task_done.mp3'
    elif event == 'SubagentStop':
        f = 'subagent_done.mp3'
    elif event == 'PreCompact':
        f = 'pre_compact.mp3'

    if f:
        path = os.path.join(sound_dir, f)
        if os.path.exists(path):
            play(path)

    print('{}')

if __name__ == '__main__':
    main()

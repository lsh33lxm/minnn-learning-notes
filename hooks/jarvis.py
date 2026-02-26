"""
JARVIS-style voice notification hook for Claude Code.
Reads hook event JSON from stdin and speaks appropriate messages
using Windows built-in TTS (System.Speech).
"""

import sys
import json
import subprocess
import os


def speak(text):
    """Use Windows built-in TTS to speak text (non-blocking)."""
    safe_text = text.replace("'", "''")  # escape single quotes for PowerShell
    ps_script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = 2; "
        f"$s.Speak('{safe_text}')"
    )
    try:
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-Command", ps_script],
            creationflags=0x08000000,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass  # fail silently, don't block Claude


def play_sound(wav_path):
    """Play a .wav file using PowerShell (non-blocking)."""
    if not os.path.exists(wav_path):
        return
    ps_script = (
        f"(New-Object Media.SoundPlayer '{wav_path}').PlaySync()"
    )
    subprocess.Popen(
        ["powershell", "-Command", ps_script],
        creationflags=0x08000000,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def notify_feishu(webhook_url, message):
    """Send a message to Feishu/Lark via webhook (optional)."""
    if not webhook_url:
        return
    payload = json.dumps({
        "msg_type": "text",
        "content": {"text": message}
    })
    subprocess.Popen(
        ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
         "-d", payload, webhook_url],
        creationflags=0x08000000,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    # --- Config ---
    # Set your Feishu webhook URL here (leave empty to disable)
    FEISHU_WEBHOOK = ""
    # Optional: path to custom .wav files (leave empty to use TTS)
    SOUND_DIR = os.path.join(os.path.dirname(__file__), "sounds")

    # --- Read hook event data from stdin ---
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    event = data.get("hook_event_name", "")

    # --- Route by event ---

    if event == "UserPromptSubmit":
        speak("Minnn, 有什么能帮你的吗")

    elif event == "Notification":
        ntype = data.get("notification_type", "")
        if ntype == "permission_prompt":
            speak("Minnn, 需要你的确认")
        else:
            speak("Minnn, 有一条新通知")

    elif event == "Stop":
        # Avoid infinite loop: check if stop hook is already active
        if data.get("stop_hook_active"):
            sys.exit(0)
        speak("Minnn, 任务已完成")
        # Optional: send Feishu notification
        if FEISHU_WEBHOOK:
            msg = data.get("last_assistant_message", "")[:200]
            notify_feishu(FEISHU_WEBHOOK, f"Claude Code 任务完成:\n{msg}")

    elif event == "SubagentStop":
        agent_type = data.get("agent_type", "子代理")
        speak(f"{agent_type} 子代理已完成")

    elif event == "PreCompact":
        trigger = data.get("trigger", "auto")
        speak(f"即将压缩上下文, 触发方式: {trigger}")

    # Output empty JSON to indicate success
    print("{}")


if __name__ == "__main__":
    main()

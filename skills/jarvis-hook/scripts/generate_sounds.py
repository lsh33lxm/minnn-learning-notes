"""
JARVIS Voice Generator - 使用 edge-tts 生成高质量科幻风语音文件。
用法: py -3 generate_sounds.py
依赖: pip install edge-tts
"""

import asyncio
import edge_tts
import os

# ============ 自定义配置 ============

# 声线选择（运行 py -3 -m edge_tts --list-voices 查看全部）
VOICE = "en-US-EricNeural"

# 音调偏移（负值=更低沉，如 "-10Hz", "-20Hz"）
PITCH = "-10Hz"

# 语速（正值=更快，如 "+12%", "+20%"）
RATE = "+12%"

# 各事件对应的语音台词
MESSAGES = {
    "prompt_submit":  "System online. At your service, Minnn.",
    "need_confirm":   "Awaiting confirmation, Minnn.",
    "task_done":      "Mission accomplished.",
    "subagent_done":  "Sub-agent protocol complete.",
    "pre_compact":    "Initiating context compression.",
    "notification":   "Incoming notification, Minnn.",
}

# ============ 生成逻辑 ============

SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")


async def generate():
    os.makedirs(SOUND_DIR, exist_ok=True)
    total = len(MESSAGES)
    for i, (name, text) in enumerate(MESSAGES.items()):
        out = os.path.join(SOUND_DIR, f"{name}.mp3")
        print(f"[{i+1}/{total}] Generating {name}.mp3 ...")
        tts = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
        await tts.save(out)
        print(f"  -> OK")
    print(f"\nAll {total} files generated in {SOUND_DIR}")


if __name__ == "__main__":
    asyncio.run(generate())

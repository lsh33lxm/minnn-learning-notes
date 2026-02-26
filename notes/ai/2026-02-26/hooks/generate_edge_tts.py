import asyncio
import edge_tts
import os

VOICE = "en-US-EricNeural"
PITCH = "-10Hz"
RATE = "+12%"
SOUND_DIR = os.path.join(os.path.dirname(__file__), "sounds")
os.makedirs(SOUND_DIR, exist_ok=True)

MESSAGES = {
    "prompt_submit":  "System online. At your service, Minnn.",
    "need_confirm":   "Awaiting confirmation, Minnn.",
    "task_done":      "Mission accomplished.",
    "subagent_done":  "Sub-agent protocol complete.",
    "pre_compact":    "Initiating context compression.",
    "notification":   "Incoming notification, Minnn.",
}

async def generate():
    for i, (name, text) in enumerate(MESSAGES.items()):
        out = os.path.join(SOUND_DIR, f"{name}.mp3")
        print(f"[{i+1}/{len(MESSAGES)}] Generating {name}.mp3")
        tts = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
        await tts.save(out)
        print(f"  -> OK")

asyncio.run(generate())
print("All 6 files regenerated!")

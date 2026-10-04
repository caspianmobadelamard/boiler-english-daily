"""تولید تمرین شنیداری + فایل صوتی"""
import os
import json
from datetime import datetime
from gtts import gTTS
from .ai_client import AIClient
from .prompts import LISTENING_PROMPT


def generate_listening_exercise(topic: str, client: AIClient) -> dict:
    prompt = LISTENING_PROMPT.format(topic=topic)
    exercise = client.generate_json(prompt)

    os.makedirs("output", exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    audio_path = f"output/listening_{date_str}.mp3"

    try:
        tts = gTTS(text=exercise["text"], lang="en", slow=False)
        tts.save(audio_path)
        exercise["audio_file"] = audio_path
    except Exception as e:
        exercise["audio_file"] = None
        exercise["tts_error"] = str(e)

    exercise["date"] = date_str
    exercise["topic"] = topic
    with open(f"output/listening_{date_str}.json", "w", encoding="utf-8") as f:
        json.dump(exercise, f, ensure_ascii=False, indent=2)

    return exercise
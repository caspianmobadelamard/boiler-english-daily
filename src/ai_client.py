"""کلاینت ارتباط با Gemini API"""
import os
import json
import re
import google.generativeai as genai


class AIClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        # حذف code block مارک‌داون
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
        return text

    def generate_text(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def generate_json(self, prompt: str) -> dict:
        full = prompt + "\n\nReturn ONLY valid JSON. No markdown, no explanation."
        response = self.model.generate_content(full)
        cleaned = self._clean_json(response.text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # تلاش دوم: پیدا کردن اولین { تا آخرین }
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                return json.loads(cleaned[start:end + 1])
            raise
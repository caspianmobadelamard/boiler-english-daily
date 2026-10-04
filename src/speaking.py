"""ارزیابی مکالمه"""
from .ai_client import AIClient
from .prompts import SPEAKING_PROMPT


def evaluate_speaking(question: str, answer: str, client: AIClient) -> dict:
    prompt = SPEAKING_PROMPT.format(question=question, answer=answer)
    return client.generate_json(prompt)
# backend_chatty20b.py
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "chatty-20b"  # your GPT-OSS model


class Chatty20BBackend:
    """
    Simple Ollama backend for Janet.
    Exposes .generate(prompt, max_tokens) as expected by Janet's organs.
    """

    def __init__(self, model: str = MODEL_NAME, url: str = OLLAMA_URL):
        self.model = model
        self.url = url

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens
            },
        }
        resp = requests.post(self.url, json=payload, timeout=600)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()

# backend_miss_gpt.py
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "deepseek-r1:14b-qwen-distill-q4_K_M"

class MissGPTBackend:
    """
    Simple wrapper around deepseek-r1 for curriculum generation.
    """

    def __init__(self, model: str = MODEL_NAME, url: str = OLLAMA_URL):
        self.model = model
        self.url = url

    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
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

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class LLMError(Exception):
    """Raised when the model call or prompt loading fails."""


def load_prompt(name):
    path = PROMPTS_DIR / f"{name}.txt"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise LLMError(f"Prompt file not found: {path}")


def _post(url, headers, payload):
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=(5, 30))
    except requests.exceptions.Timeout:
        raise LLMError("The model provider timed out.")
    except requests.exceptions.RequestException as e:
        raise LLMError(f"Could not reach the model provider: {e}")
    if resp.status_code >= 400:
        raise LLMError(f"Provider returned {resp.status_code}: {resp.text[:200]}")
    return resp.json()


def _groq(system, user):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is not set in .env")
    data = _post(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Authorization": f"Bearer {key}"},
        {
            "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        },
    )
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise LLMError("Groq returned an unexpected response format.")
    if not content or not content.strip():
        raise LLMError("The model returned an empty answer. Try again.")
    return content


def _gemini(system, user):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise LLMError("GEMINI_API_KEY is not set in .env")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    data = _post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        {"x-goog-api-key": key},
        {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.2,
                                 "responseMimeType": "application/json"},
        },
    )
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise LLMError("Gemini returned no text (possibly blocked or empty).")


def chat_completion(system, user):
    """Send a system + user prompt to the provider chosen in .env."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider == "groq":
        return _groq(system, user)
    if provider == "gemini":
        return _gemini(system, user)
    raise LLMError(f"Unknown LLM_PROVIDER '{provider}' (use groq or gemini)")
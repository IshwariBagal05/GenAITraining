
import logging
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

logger = logging.getLogger(__name__)


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


def _groq_with_usage(system, user):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is not set in .env")

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    data = _post(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Authorization": f"Bearer {key}"},
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
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

    usage = data.get("usage", {})

    return content, {
        "provider": "groq",
        "model": model,
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def _gemini_with_usage(system, user):
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
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        },
    )

    try:
        content = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise LLMError("Gemini returned no text (possibly blocked or empty).")

    if not content or not content.strip():
        raise LLMError("The model returned an empty answer. Try again.")

    usage = data.get("usageMetadata", {})

    return content, {
        "provider": "gemini",
        "model": model,
        "input_tokens": usage.get("promptTokenCount"),
        "output_tokens": usage.get("candidatesTokenCount"),
        "total_tokens": usage.get("totalTokenCount"),
    }


def chat_completion_with_usage(system, user):
    """Call the selected provider and return text with usage information."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    start_time = time.perf_counter()

    if provider == "groq":
        content, usage = _groq_with_usage(system, user)
    elif provider == "gemini":
        content, usage = _gemini_with_usage(system, user)
    else:
        raise LLMError(
            f"Unknown LLM_PROVIDER '{provider}' (use groq or gemini)"
        )

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
        "LLM request completed | provider=%s | model=%s | latency_ms=%s "
        "| input_tokens=%s | output_tokens=%s | total_tokens=%s",
        usage["provider"],
        usage["model"],
        latency_ms,
        usage["input_tokens"],
        usage["output_tokens"],
        usage["total_tokens"],
    )

    return content, usage


def chat_completion(system, user):
    """Backward-compatible function returning only the model's text."""
    content, _ = chat_completion_with_usage(system, user)
    return content

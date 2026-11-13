import json
import re

from app.llm import LLMError, chat_completion, load_prompt
from app.records import load_records
from app.smart_search import rank

RECORDS = load_records()

TASK_FILES = {"v1": "task_v1_basic", "v2": "task_v2_grounded"}
VALID_CONFIDENCE = {"low", "medium", "high"}


def build_context(matches):
    if not matches:
        return "No matching records found."
    return "\n".join(
        f"[{m['topic']}] Rule: {m['rule_summary']} | Time limit: {m['time_limit']} "
        f"| Contact: {m['who_to_contact']} | Source: {m['source_url']}"
        for m in matches
    )


def parse_json(text):
    """Pull the JSON object out of the model's reply (handles ``` fences)."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start:end + 1])


def answer_question(question, version="v2", top_k=3):
    if version not in TASK_FILES:
        raise LLMError(f"Unknown prompt version '{version}'")

    ranked = rank(RECORDS, question, top_k=top_k)
    top_score = ranked[0]["score"] if ranked else 0
    matches = [m for m in ranked if m["score"] >= max(0.05, 0.5 * top_score)]
    system = load_prompt("system")
    task = (load_prompt(TASK_FILES[version])
            .replace("{context}", build_context(matches))
            .replace("{question}", question))

    raw = chat_completion(system, task)

    try:
        data = parse_json(raw)
        answer = str(data.get("answer", "")).strip()
        confidence = str(data.get("confidence", "low")).lower()
        follow_up = str(data.get("follow_up", "")).strip()
    except (ValueError, json.JSONDecodeError):
        # the model ignored the JSON format: return its text, marked low confidence
        answer, confidence, follow_up = raw.strip()[:600], "low", ""

    if confidence not in VALID_CONFIDENCE:
        confidence = "low"
    if not answer:
        answer, confidence = "I could not produce an answer. Please try rephrasing.", "low"

    sources = [{"topic": m["topic"], "source_url": m["source_url"]}
               for m in matches]
    if confidence == "low":
        sources = []          # a "cannot answer" reply should not cite sources

    return {
        "answer": answer,
        "confidence": confidence,
        "follow_up": follow_up,
        "sources": sources,
    }
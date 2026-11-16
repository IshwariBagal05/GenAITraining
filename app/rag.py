import json
import re
import time

from app.chat import parse_json
from app.chunking import load_chunks
from app.embed import embed_texts, search_matrix
from app.llm import LLMError, chat_completion, load_prompt

# Update these two numbers to the winning config after you run the evaluation.
DEFAULT_CONFIG = {"max_chars": 700, "top_k": 3}

IDK_ANSWER = ("I don't know. The IRDAI pages I have do not cover this. "
              "You can ask your insurer, call IRDAI toll free 155-255, "
              "or contact the Insurance Ombudsman.")

_index_cache = {}


def get_index(max_chars):
    """Chunk all pages at this size and embed them once (cached per size)."""
    if max_chars not in _index_cache:
        chunks = load_chunks(max_chars)
        if not chunks:
            raise RuntimeError("No chunks found. Check data/raw/ and app/ingest.py.")
        # the title in front of each chunk helps short questions find the right page
        texts = [f"{c['title']}. {c['text']}" for c in chunks]
        _index_cache[max_chars] = (chunks, embed_texts(texts))
    return _index_cache[max_chars]


def retrieve(question, max_chars, top_k):
    chunks, matrix = get_index(max_chars)
    return search_matrix(question, chunks, matrix, top_k=top_k)


def build_context(hits):
    return "\n\n".join(f"[S{i}] ({h['title']}) {h['text']}"
                       for i, h in enumerate(hits, start=1))


def call_llm(system, user, tries=4):
    """Call the model, waiting and retrying when the free tier says 429."""
    for attempt in range(tries):
        try:
            return chat_completion(system, user)
        except LLMError as e:
            if "429" in str(e) and attempt < tries - 1:
                time.sleep(25 * (attempt + 1))
                continue
            raise


def _idk(hits):
    return {
        "answer": IDK_ANSWER,
        "answerable": False,
        "citations": [],
        "confidence": "low",
        "retrieved": [{"title": h["title"], "slug": h["slug"], "score": h["score"]}
                      for h in hits],
    }


def ask(question, config=None):
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    hits = retrieve(question, cfg["max_chars"], cfg["top_k"])
    system = load_prompt("rag_system")
    user = (load_prompt("rag_task")
            .replace("{context}", build_context(hits))
            .replace("{question}", question))

    raw = call_llm(system, user)
    try:
        data = parse_json(raw)
    except (ValueError, json.JSONDecodeError):
        return _idk(hits)           # unreadable reply: do not trust it

    answer = str(data.get("answer", "")).strip()
    answerable = data.get("answerable") is True

    # keep only citations that point at a source we really sent
    cited, seen = [], set()
    for label in data.get("citations") or []:
        for num in re.findall(r"\d+", str(label)):
            n = int(num)
            if 1 <= n <= len(hits) and n not in seen:
                seen.add(n)
                h = hits[n - 1]
                cited.append({"label": f"S{n}", "title": h["title"],
                              "slug": h["slug"], "source": h["source"],
                              "page": h["page"], "snippet": h["text"][:200]})

    text = answer.replace("\u2019", "'").lower()
    if not answerable or not cited or not answer or text.startswith("i don't know"):
        return _idk(hits)

    confidence = str(data.get("confidence", "medium")).lower()
    if confidence not in {"low", "medium", "high"}:
        confidence = "medium"

    return {
        "answer": answer,
        "answerable": True,
        "citations": cited,
        "confidence": confidence,
        "retrieved": [{"title": h["title"], "slug": h["slug"], "score": h["score"]}
                      for h in hits],
    }
import json
import sys
from datetime import date

from app.chat import parse_json
from app.llm import load_prompt
from app.rag import call_llm
from app.tools import call_tool, describe_tools

MAX_STEPS = 5
GIVE_UP = "I could not finish this request. Please rephrase it, or ask your insurer."
IDK = ("I don't know. The IRDAI pages I have do not cover this. You can ask your insurer, "
       "call IRDAI toll free 155-255, or contact the Insurance Ombudsman.")


def build_system():
    return (load_prompt("agent_system")
            .replace("{today}", date.today().isoformat())
            .replace("{tools}", describe_tools()))


def render(messages):
    """Turn the message list into one text transcript for the model."""
    lines = [f"{m['role'].upper()}: {m['content']}" for m in messages]
    return "\n\n".join(lines) + "\n\nASSISTANT (reply with one JSON object):"


def observation_text(observation, limit=1800):
    text = json.dumps(observation, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + "...(truncated)"


def decide(messages):
    """Ask the model what to do next. Returns a dict with an 'action' key."""
    raw = call_llm(build_system(), render(messages))
    try:
        return parse_json(raw)
    except ValueError:                      # includes json.JSONDecodeError
        return {"action": "invalid", "raw": raw[:200]}


def sources_from(name, observation):
    if name != "rag_search" or not observation.get("ok"):
        return []
    return [{"title": h["title"], "source": h["source"]} for h in observation["result"]]


def finalize(decision, tools_ok, sources):
    """Turn the model's final decision into a safe answer dict."""
    answer = str(decision.get("answer", "")).strip()
    answerable = decision.get("answerable") is True
    confidence = str(decision.get("confidence", "medium")).lower()
    if confidence not in {"low", "medium", "high"}:
        confidence = "medium"

    if not answer:
        return {"answer": IDK, "answerable": False, "confidence": "low", "sources_consulted": []}
    # strict guard: a rules answer with no successful tool call is not trusted,
    # unless the agent is only asking the user for missing details
    if answerable and not tools_ok and not answer.endswith("?"):
        return {"answer": IDK, "answerable": False, "confidence": "low", "sources_consulted": []}
    if not answerable and not answer.replace("\u2019", "'").lower().startswith("i don't know"):
        answer = "I don't know. " + answer

    seen, unique = set(), []
    for s in sources:
        if s["source"] not in seen:
            seen.add(s["source"])
            unique.append(s)
    return {"answer": answer, "answerable": answerable, "confidence": confidence,
            "sources_consulted": unique}


def run_agent(question, history=None, max_steps=MAX_STEPS):
    messages = list(history or []) + [{"role": "user", "content": question}]
    trace, sources, seen_calls = [], [], set()

    for step in range(1, max_steps + 1):
        decision = decide(messages)
        action = decision.get("action")

        if action == "final":
            result = finalize(decision, any(t["ok"] for t in trace), sources)
            messages.append({"role": "assistant", "content": result["answer"]})
            return {**result, "trace": trace, "messages": messages}

        if action == "tool":
            name = decision.get("tool")
            args = decision.get("args") or {}
            key = (name, json.dumps(args, sort_keys=True, default=str))
            if key in seen_calls:
                observation = {"ok": False, "error": "You already made this exact call. "
                                                     "Use the earlier result or give the final answer."}
            else:
                seen_calls.add(key)
                observation = call_tool(name, args)
            sources += sources_from(name, observation)
            trace.append({"step": step, "tool": name, "args": args, "ok": observation["ok"]})
            messages.append({"role": "assistant", "content": json.dumps(decision, ensure_ascii=False)})
            messages.append({"role": "tool", "content": observation_text(observation)})
            continue

        messages.append({"role": "user", "content":
                         "Your last reply was not a valid JSON object in the required format. "
                         "Reply with one JSON object."})

    return {"answer": GIVE_UP, "answerable": False, "confidence": "low",
            "sources_consulted": [], "trace": trace, "messages": messages}


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is portability in health insurance?"
    out = run_agent(question)
    print("\nTRACE")
    for t in out["trace"]:
        print(f"  step {t['step']}: {t['tool']} {json.dumps(t['args'], ensure_ascii=False)}  ok={t['ok']}")
    print(f"\nANSWER ({out['confidence']}, answerable={out['answerable']}):\n{out['answer']}")
import json
import sys
import time
from pathlib import Path

from app.rag import ask, get_index, retrieve

ROOT = Path(__file__).resolve().parent.parent
EVAL_SET = ROOT / "eval" / "eval_set.json"
OUT = ROOT / "eval" / "eval_results.md"

# The two configs to compare. Edit the numbers if you want other values.
CONFIGS = [
    {"name": "A", "max_chars": 400, "top_k": 3},
    {"name": "B", "max_chars": 900, "top_k": 5},
]


def pct(x):
    return "n/a" if x is None else f"{round(100 * x)}%"


def short(text, n=60):
    text = " ".join(text.split()).replace("|", "/")
    return text if len(text) <= n else text[:n] + "..."


def evaluate(config, rows, retrieval_only):
    max_chars, top_k = config["max_chars"], config["top_k"]
    chunks, _ = get_index(max_chars)
    per_q = []
    for row in rows:
        expected = set(row["expected_slugs"])
        hits = retrieve(row["question"], max_chars, top_k)
        retrieved = [h["slug"] for h in hits]
        item = {"id": row["id"], "answerable": row["answerable"],
                "retrieved": retrieved,
                "hit": bool(expected & set(retrieved)) if row["answerable"] else None,
                "correct": None, "note": ""}
        if not retrieval_only:
            try:
                res = ask(row["question"], {"max_chars": max_chars, "top_k": top_k})
            except Exception as e:
                item["correct"] = False
                item["note"] = f"ERROR {short(str(e), 50)}"
            else:
                answer = res["answer"].lower()
                if row["answerable"]:
                    keyword = any(k.lower() in answer for k in row["must_contain_any"])
                    cited = any(c["slug"] in expected for c in res["citations"])
                    item["correct"] = res["answerable"] and keyword and cited
                    item["note"] = ("ok" if item["correct"] else
                                    "refused" if not res["answerable"] else
                                    "keyword missing" if not keyword else "wrong source")
                else:
                    item["correct"] = not res["answerable"]
                    item["note"] = "said I don't know" if item["correct"] else "ANSWERED (should not)"
            time.sleep(4)
        per_q.append(item)

    ans = [q for q in per_q if q["answerable"]]
    uns = [q for q in per_q if not q["answerable"]]
    summary = {
        "name": config["name"], "max_chars": max_chars, "top_k": top_k,
        "chunks": len(chunks),
        "retrieval_hit": sum(q["hit"] for q in ans) / len(ans),
        "answer_acc": None, "idk_acc": None, "overall": None,
    }
    if not retrieval_only:
        summary["answer_acc"] = sum(bool(q["correct"]) for q in ans) / len(ans)
        summary["idk_acc"] = sum(bool(q["correct"]) for q in uns) / len(uns)
        summary["overall"] = sum(bool(q["correct"]) for q in per_q) / len(per_q)
    return summary, per_q


def main():
    retrieval_only = "--retrieval-only" in sys.argv
    rows = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    print(f"{len(rows)} questions, {len(CONFIGS)} configs, "
          f"{'retrieval only' if retrieval_only else 'full RAG'}")

    summaries, details = [], []
    for cfg in CONFIGS:
        print(f"Config {cfg['name']}: chunk size {cfg['max_chars']}, top-k {cfg['top_k']}")
        s, per_q = evaluate(cfg, rows, retrieval_only)
        summaries.append(s)
        details.append(per_q)

    lines = ["| Config | Chunk size | top-k | Chunks | Retrieval hit | Answer accuracy "
             "| \"I don't know\" accuracy | Overall |",
             "|---|---|---|---|---|---|---|---|"]
    for s in summaries:
        lines.append(f"| {s['name']} | {s['max_chars']} | {s['top_k']} | {s['chunks']} "
                     f"| {pct(s['retrieval_hit'])} | {pct(s['answer_acc'])} "
                     f"| {pct(s['idk_acc'])} | {pct(s['overall'])} |")
    table = "\n".join(lines)

    winner_line = ""
    if not retrieval_only:
        best = max(summaries, key=lambda s: (s["overall"], s["retrieval_hit"], -s["top_k"]))
        winner_line = (f"Winner: config {best['name']} (chunk size {best['max_chars']}, "
                       f"top-k {best['top_k']}) with {pct(best['overall'])} overall.")

    per_lines = ["| # | Question | Answerable | " +
                 " | ".join(f"{c['name']} retrieved | {c['name']} result" for c in CONFIGS) + " |",
                 "|---|---|---|" + "---|---|" * len(CONFIGS)]
    for i, row in enumerate(rows):
        cells = []
        for per_q in details:
            q = per_q[i]
            result = q["note"] if not retrieval_only else (
                "hit" if q["hit"] else ("miss" if q["hit"] is False else "-"))
            cells.append(f"{', '.join(dict.fromkeys(q['retrieved']))} | {result}")
        per_lines.append(f"| {row['id']} | {short(row['question'])} | "
                         f"{'yes' if row['answerable'] else 'no'} | " + " | ".join(cells) + " |")

    OUT.write_text("\n".join([
        "# Evaluation: 2 configs on 15 questions", "",
        "Retrieval hit = a retrieved chunk came from an expected page (answerable questions).",
        "Answer accuracy = answerable, keyword present and cited an expected page.",
        "\"I don't know\" accuracy = unanswerable questions correctly refused.", "",
        table, "", winner_line, "", "## Per question", "", *per_lines, ""]),
        encoding="utf-8")

    print("\n" + table)
    if winner_line:
        print("\n" + winner_line)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
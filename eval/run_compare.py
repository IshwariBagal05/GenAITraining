import re
import time
from pathlib import Path

from app.chat import answer_question

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = ROOT / "docs" / "questions.md"
OUT = ROOT / "eval" / "prompt_compare.md"


def load_questions():
    rows = []
    for line in QUESTIONS_FILE.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].isdigit():
            rows.append((int(cells[0]), cells[1], cells[2]))
    return rows


def short(text, n=220):
    text = text.replace("\u2011", "-").replace("\u2019", "'")
    text = re.sub(r"\s+", " ", text).replace("|", "/")
    return text if len(text) <= n else text[:n] + "..."


def run(question, version):
    for attempt in range(4):
        try:
            r = answer_question(question, version)
            return f"**{r['confidence']}**: {short(r['answer'])}"
        except Exception as e:
            if "429" in str(e) and attempt < 3:
                wait = 25 * (attempt + 1)
                print(f"   rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            return f"ERROR: {short(str(e), 100)}"


def main():
    questions = load_questions()
    if len(questions) < 10:
        print(f"Only {len(questions)} questions parsed from {QUESTIONS_FILE}")
    lines = [
        "# Prompt comparison: v1 (basic) vs v2 (grounded)",
        "",
        "Same system prompt, same retrieval (top 3 records), same model. "
        "Only the task prompt differs.",
        "",
        "| # | Question | Should it answer? | v1 basic | v2 grounded | Better |",
        "|---|----------|-------------------|----------|-------------|--------|",
    ]
    for num, question, expected in questions:
        print(f"Q{num}...")
        v1 = run(question, "v1")
        time.sleep(2)
        v2 = run(question, "v2")
        time.sleep(2)
        lines.append(f"| {num} | {short(question, 90)} | {short(expected, 40)} "
                     f"| {v1} | {v2} |  |")

    lines += [
        "",
        "## My analysis",
        "",
        "TODO after reading the table: write 4 to 6 lines.",
        "- Which prompt followed the rules better, and on which questions?",
        "- What did v2 do on Q6 and Q10 (the questions my data cannot answer)?",
        "- Did either prompt invent a number, company or hospital?",
        "- Which prompt do I keep, and what would I change next?",
    ]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
import re
from pathlib import Path

from app.chunking import load_chunks
from app.embed import embed_texts, search_matrix

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = ROOT / "docs" / "questions.md"
OUT = ROOT / "eval" / "search_results.md"


def load_questions():
    rows = []
    for line in QUESTIONS_FILE.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].isdigit():
            rows.append((int(cells[0]), cells[1], cells[2]))
    return rows


def clean(text, n):
    text = re.sub(r"\s+", " ", text).replace("|", "/")
    return text if len(text) <= n else text[:n] + "..."


def main():
    chunks = load_chunks()
    matrix = embed_texts([c["text"] for c in chunks])
    questions = load_questions()
    print(f"{len(chunks)} chunks, {len(questions)} questions")

    table = [
        "| # | Question | Should it answer? | Hit 1 | Hit 2 | Hit 3 | Top hit relevant? |",
        "|---|----------|-------------------|-------|-------|-------|-------------------|",
    ]
    details = []
    for num, question, expected in questions:
        hits = search_matrix(question, chunks, matrix, top_k=3)
        cells = [f"{h['title']} ({h['score']:.2f})" for h in hits]
        table.append(f"| {num} | {clean(question, 80)} | {clean(expected, 30)} | "
                     f"{' | '.join(cells)} |  |")
        details.append(f"### Q{num}: {clean(question, 120)}\n")
        for rank_no, h in enumerate(hits, start=1):
            details.append(f"{rank_no}. **{h['title']}** (score {h['score']:.4f}, "
                           f"page {h['page']}) {h['source']}  \n"
                           f"   {clean(h['text'], 220)}")
        details.append("")

    lines = [
        "# Semantic search results (embeddings, top 3 chunks per question)",
        "",
        f"Chunks searched: {len(chunks)}. Score is cosine similarity, higher is closer.",
        "",
        *table,
        "",
        "## Details",
        "",
        *details,
        "## My notes",
        "",
        "TODO after reading the table: write 4 to 6 lines.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
import re
from pathlib import Path

from app.fetch import SOURCES
from app.ingest import extract_content

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
MAX_CHARS = 700


def _split_long(text, max_chars):
    """Split one very long block on sentence boundaries."""
    parts, cur = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if cur and len(cur) + len(sentence) + 1 > max_chars:
            parts.append(cur)
            cur = sentence
        else:
            cur = f"{cur} {sentence}".strip()
    if cur:
        parts.append(cur)
    return parts


def chunk_blocks(blocks, max_chars=MAX_CHARS):
    """Pack text blocks into chunks of at most about max_chars characters."""
    pieces = []
    for b in blocks:
        pieces.extend(_split_long(b, max_chars) if len(b) > max_chars else [b])

    chunks, cur = [], ""
    for p in pieces:
        if cur and len(cur) + len(p) + 1 > max_chars:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur} {p}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def load_chunks():
    """Chunk every saved page. Each chunk keeps source, page and title."""
    chunks = []
    for path in sorted(RAW_DIR.glob("*.html")):
        slug = path.stem
        try:
            title, blocks = extract_content(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[SKIPPED] {slug}: {e}")
            continue
        for i, text in enumerate(chunk_blocks(blocks)):
            chunks.append({
                "id": f"{slug}-{i}",
                "text": text,
                "source": SOURCES.get(slug, ""),
                "page": 1,
                "title": title,
                "slug": slug,
                "chunk_index": i,
            })
    return chunks


if __name__ == "__main__":
    all_chunks = load_chunks()
    print(f"{len(all_chunks)} chunks from {len({c['slug'] for c in all_chunks})} pages\n")
    for c in all_chunks[:2]:
        print(f"[{c['id']}] {c['title']} | page {c['page']} | {c['source']}")
        print(f"   {c['text'][:200]}...\n")
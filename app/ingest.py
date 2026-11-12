import json
import re
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

from app.fetch import SOURCES
from app.models import Record

RAW_DIR = Path("data/raw")
OUT_FILE = Path("data/records.json")

TYPE_HINTS = {"claim": "General/Claims", "free-look": "Life/Health",
              "portab": "Health", "renewab": "Health",
              "ulip": "Life", "motor": "Motor"}

TIME_RE = re.compile(r"\b\d+\s*(days?|months?|years?)\b", re.I)


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def guess_type(slug):
    for key, value in TYPE_HINTS.items():
        if key in slug:
            return value
    return "General"


def extract_blocks(html):
    """All reasonably long text blocks on a page, in order, without duplicates."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "noscript", "form", "select"]):
        tag.decompose()

    blocks = []
    for el in soup.find_all(["p", "li", "td", "div"]):
        # for a div, only take "leaf" divs so text is not counted twice
        if el.name == "div" and el.find(["p", "li", "td", "div"]):
            continue
        text = clean(el.get_text(" "))
        if len(text) >= 60 and text not in blocks:
            blocks.append(text)
    return blocks


def pick_summary(slug, blocks):
    """Prefer blocks that mention the topic words or a time period."""
    words = [w for w in slug.split("-") if len(w) > 3]

    def score(b):
        low = b.lower()
        return sum(w in low for w in words) + (2 if TIME_RE.search(b) else 0)

    ranked = sorted(range(len(blocks)), key=lambda i: -score(blocks[i]))
    best = sorted(ranked[:3])               # keep original page order
    return " ".join(blocks[i] for i in best)[:500]


def find_time_limit(blocks):
    for b in blocks:
        m = TIME_RE.search(b)
        if m:
            return m.group(0)
    return "Not specified"


def find_contact(blocks):
    keys = ("grievance", "ombudsman", "bima bharosa", "complaint", "contact")
    for b in blocks:
        if any(k in b.lower() for k in keys):
            return b[:200]
    return "Not specified"


def ingest():
    pages = {}
    for path in sorted(RAW_DIR.glob("*.html")):
        try:
            pages[path.stem] = extract_blocks(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[SKIPPED] {path.stem}: {e}")

    # text that appears on more than half of the pages is menu/footer boilerplate
    freq = Counter(b for blocks in pages.values() for b in set(blocks))
    limit = max(2, len(pages) // 2 + 1)
    boilerplate = {b for b, n in freq.items() if n >= limit}

    records, skipped = [], 0
    for slug, blocks in pages.items():
        try:
            unique = [b for b in blocks if b not in boilerplate]
            if not unique:
                raise ValueError("no page-specific text found")
            records.append(Record(
                topic=slug.replace("-", " ").title(),
                insurance_type=guess_type(slug),
                rule_summary=pick_summary(slug, unique),
                time_limit=find_time_limit(unique),
                who_to_contact=find_contact(unique),
                source_url=SOURCES.get(slug, ""),
            ))
            print(f"[OK] {slug}")
        except Exception as e:
            skipped += 1
            print(f"[SKIPPED] {slug}: {e}")

    OUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in records], f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(records)} records to {OUT_FILE} ({skipped} skipped)")


if __name__ == "__main__":
    ingest()
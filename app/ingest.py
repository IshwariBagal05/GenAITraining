import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

from app.fetch import SOURCES
from app.models import Record

RAW_DIR = Path("data/raw")
OUT_FILE = Path("data/records.json")

TYPE_HINTS = {
    "claim": "General/Claims",
    "free-look": "Life/Health",
    "portability": "Health",
    "renewab": "Health",
    "ulip": "Life",
    "motor": "Motor",
}


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def guess_type(slug):
    for key, value in TYPE_HINTS.items():
        if key in slug:
            return value
    return "General"


def find_time_limit(paragraphs):
    pattern = re.compile(r"\b(\d+)\s*(days?|months?|years?)\b", re.I)
    for p in paragraphs:
        m = pattern.search(p)
        if m:
            return m.group(0)
    return "Not specified"


def find_contact(paragraphs):
    keywords = ("contact", "grievance", "ombudsman", "bima bharosa", "complaint")
    for p in paragraphs:
        if any(k in p.lower() for k in keywords):
            return p[:200]
    return "Not specified"


def parse_page(slug, html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    h1 = soup.find("h1")
    topic = clean(h1.get_text()) if h1 else slug.replace("-", " ").title()

    main = soup.find("main") or soup.body
    paragraphs = []
    for el in main.find_all(["p", "li"]):
        text = clean(el.get_text(" "))
        if len(text) > 40:
            paragraphs.append(text)

    if not paragraphs:
        raise ValueError("no usable text found")

    return Record(
        topic=topic,
        insurance_type=guess_type(slug),
        rule_summary=" ".join(paragraphs[:3])[:500],
        time_limit=find_time_limit(paragraphs),
        who_to_contact=find_contact(paragraphs),
        source_url=SOURCES.get(slug, ""),
    )


def ingest():
    records, skipped = [], 0
    for path in sorted(RAW_DIR.glob("*.html")):
        slug = path.stem
        try:
            html = path.read_text(encoding="utf-8")
            records.append(parse_page(slug, html))
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
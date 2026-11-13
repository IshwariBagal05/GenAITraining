import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

from app.fetch import SOURCES
from app.models import Record

RAW_DIR = Path("data/raw")
OUT_FILE = Path("data/records.json")

FOOTER_HEADINGS = {"quick links", "irdai head office", "regional offices",
                   "toll free number", "follow us on"}

TYPE_HINTS = {"claim": "General/Claims", "free-look": "Life/Health",
              "portab": "Health", "renewab": "Health", "griev": "General",
              "bharosa": "General", "ulip": "Life", "motor": "Motor"}

TIME_RE = re.compile(r"\b\d+\s*(days?|months?|years?)\b", re.I)


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def guess_type(slug):
    for key, value in TYPE_HINTS.items():
        if key in slug:
            return value
    return "General"


def norm(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def extract_content(html):
    """Return (topic, blocks): text under the h2 that matches the page title,
    stopping at the next h2 or the footer."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "noscript"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    topic = title.removesuffix(" - Policy Holder - IRDAI").strip()
    if not topic:
        raise ValueError("page has no title")

    h2s = soup.find_all("h2")
    heading = None
    for i, h in enumerate(h2s):
        # the banner h2 starts with the topic name; the content h2 comes next
        if norm(clean(h.get_text(" "))).startswith(norm(topic)):
            if i + 1 < len(h2s):
                heading = h2s[i + 1]
            break
    if heading is None:
        raise ValueError(f"no content heading found for '{topic}'")

    footer = None
    for h in soup.find_all("h3"):
        if clean(h.get_text(" ")).lower() in FOOTER_HEADINGS:
            footer = h
            break

    blocks = []
    for el in heading.next_elements:
        if footer is not None and el is footer:
            break
        name = getattr(el, "name", None)
        if name == "h2":
            break
        if name not in ("p", "li", "td", "div"):
            continue
        if name == "div" and el.find(["p", "li", "td", "div"]):
            continue
        text = clean(el.get_text(" "))
        if len(text) >= 40 and not any(text in b for b in blocks):
            blocks.append(text)

    if not blocks:
        raise ValueError(f"no text under the '{topic}' heading")
    return topic, blocks


def find_time_limit(blocks):
    for b in blocks:
        m = TIME_RE.search(b)
        if m:
            return m.group(0)
    return "Not specified"


DEFAULT_CONTACT = "Your insurer's grievance officer; IRDAI toll free 155-255"


def find_contact(blocks):
    keys = ("grievance", "ombudsman", "bima bharosa", "complaint", "contact")
    for b in blocks:
        if any(k in b.lower() for k in keys):
            return re.sub(r"^\d+\s+", "", b)[:200]
    return DEFAULT_CONTACT


def ingest():
    records, skipped = [], 0
    for path in sorted(RAW_DIR.glob("*.html")):
        slug = path.stem
        try:
            topic, blocks = extract_content(path.read_text(encoding="utf-8"))
            records.append(Record(
                topic=topic,
                insurance_type=guess_type(slug),
                rule_summary=re.sub(r"^\d+\s+", "", " ".join(blocks[:2]))[:500],
                time_limit=find_time_limit(blocks),
                who_to_contact=find_contact(blocks),
                source_url=SOURCES.get(slug, ""),
            ))
            print(f"[OK] {slug}: {len(blocks)} text blocks")
        except Exception as e:
            skipped += 1
            print(f"[SKIPPED] {slug}: {e}")

    OUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in records], f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(records)} records to {OUT_FILE} ({skipped} skipped)")


if __name__ == "__main__":
    ingest()
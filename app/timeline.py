import json
import re
import sys
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from app.chunking import load_chunks
from app.fetch import SOURCES
from app.tools import FREE_LOOK_DAYS

TIMELINE_FILE = Path(__file__).resolve().parent.parent / "data" / "timeline.json"
POLICY_TYPES = ["life", "health", "motor"]
FREE_LOOK_PAGES = ["free-look-period", "distance-marketing"]
REQUIRED = {"key", "label", "day_text", "detail", "sources"}


def norm(text):
    """Lowercase letters and digits only, so spacing and punctuation never block a match."""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


@lru_cache(maxsize=1)
def _page_texts():
    pages = {}
    for chunk in load_chunks(900):
        pages[chunk["slug"]] = pages.get(chunk["slug"], "") + " " + chunk["text"]
    return {slug: norm(text) for slug, text in pages.items()}


def phrase_on_page(slug, phrase):
    return norm(phrase) in _page_texts().get(slug, "")


def load_timeline():
    data = json.loads(TIMELINE_FILE.read_text(encoding="utf-8"))
    for ptype in POLICY_TYPES:
        if ptype not in data:
            raise ValueError(f"timeline.json has no '{ptype}' section")
        for step in data[ptype]:
            missing = REQUIRED - set(step)
            if missing:
                raise ValueError(f"timeline.json: step '{step.get('key')}' ({ptype}) "
                                 f"is missing {sorted(missing)}")
    return data


def build_timeline(policy_type, sold_via, received=None):
    """Steps for one policy type, with real dates and a check of every source."""
    data = load_timeline()
    if policy_type not in data:
        raise ValueError(f"No timeline for policy type '{policy_type}'")
    steps = []
    for raw in data[policy_type]:
        step = dict(raw)
        step["days_on_page"] = None
        if step["key"] == "received":
            step["day"] = 0
        elif step["key"] == "free_look_ends" and policy_type != "motor":
            days = FREE_LOOK_DAYS[sold_via]          # same numbers as the calculator
            step["day"] = days
            step["day_text"] = f"Day {days}"
            step["days_on_page"] = any(phrase_on_page(slug, f"{days} days")
                                       for slug in FREE_LOOK_PAGES)
        step.setdefault("day", None)
        step["date"] = ((received + timedelta(days=step["day"])).isoformat()
                        if received and step["day"] is not None else None)
        step["sources_checked"] = [
            {"slug": s["slug"], "url": SOURCES.get(s["slug"], ""),
             "evidence": s["evidence"], "found": phrase_on_page(s["slug"], s["evidence"])}
            for s in step["sources"]]
        steps.append(step)
    return steps


def find(keyword):
    """Print sentences from your pages that mention the keyword AND a number of days, months..."""
    number = re.compile(r"\b\d+\s*(days?|months?|years?|hours?)\b", re.I)
    kw = keyword.lower()
    count = 0
    for chunk in load_chunks(900):
        for sentence in re.split(r"(?<=[.!?])\s+", chunk["text"]):
            if kw in sentence.lower() and number.search(sentence):
                print(f"[{chunk['slug']}] {sentence.strip()}\n")
                count += 1
    print(f"{count} sentence(s) found")


def check():
    problems = 0
    for ptype in POLICY_TYPES:
        print(f"\n== {ptype} ==")
        for step in build_timeline(ptype, "offline"):
            for s in step["sources_checked"]:
                problems += not s["found"]
                print(f"  {'OK     ' if s['found'] else 'MISSING'} {step['key']:17} "
                      f"{s['slug']}: \"{s['evidence']}\"")
    print("\n== free-look day counts (from app/tools.py) found on the pages? ==")
    for sold, days in FREE_LOOK_DAYS.items():
        pages = [slug for slug in FREE_LOOK_PAGES if phrase_on_page(slug, f"{days} days")]
        problems += not pages
        print(f"  {sold:10} {days} days -> "
              f"{'found on ' + ', '.join(pages) if pages else 'NOT FOUND on the pages'}")
    print(f"\n'motor' mentioned on the free-look page: "
          f"{phrase_on_page('free-look-period', 'motor')} (the motor timeline assumes False)")
    print(f"\n{problems} problem(s)")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "find":
        find(" ".join(sys.argv[2:]))
    else:
        check()
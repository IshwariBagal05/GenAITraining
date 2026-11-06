import json
from collections import Counter
from pathlib import Path

DEFAULT_PATH = Path("data/sample_records.json")


def load_records(path=DEFAULT_PATH):
    """Load records from a JSON file. Returns [] if the file is missing or invalid."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {path}: {e}")
        return []


def search(records, keyword):
    """Return records whose topic or rule_summary contains the keyword."""
    kw = keyword.lower().strip()
    return [
        r for r in records
        if kw in r.get("topic", "").lower()
        or kw in r.get("rule_summary", "").lower()
    ]


def count_by(records, field):
    """Count records per value of a field, e.g. count_by(records, 'insurance_type')."""
    return dict(Counter(r.get(field, "Unknown") for r in records))


def get_by_id(records, record_id):
    """Return the record with the given id, or None."""
    for r in records:
        if r.get("id") == record_id:
            return r
    return None
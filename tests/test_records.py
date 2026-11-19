import json

from app.records import count_by, get_by_id, load_records, search


def test_load_records_reads_json(tmp_path):
    path = tmp_path / "records.json"
    expected = [{"id": 1, "topic": "Portability"}]
    path.write_text(json.dumps(expected), encoding="utf-8")

    assert load_records(path) == expected


def test_load_records_returns_empty_for_missing_file(tmp_path):
    assert load_records(tmp_path / "missing.json") == []


def test_search_matches_topic_and_summary_case_insensitively():
    records = [
        {"topic": "Portability", "rule_summary": "Move a policy"},
        {"topic": "Renewal", "rule_summary": "Port existing benefits"},
        {"topic": "Claims", "rule_summary": "Send documents"},
    ]

    assert search(records, " PORT ") == records[:2]


def test_count_by_and_get_by_id():
    records = [
        {"id": 1, "insurance_type": "Health"},
        {"id": 2, "insurance_type": "Health"},
        {"id": 3},
    ]

    assert count_by(records, "insurance_type") == {"Health": 2, "Unknown": 1}
    assert get_by_id(records, 2) == records[1]
    assert get_by_id(records, 99) is None

from fastapi.testclient import TestClient

from app import main
from app.main import app

client = TestClient(app)


def test_health_reports_loaded_record_count(monkeypatch):
    monkeypatch.setattr(main, "RECORDS", [{"id": 1}, {"id": 2}])

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "records_loaded": 2}


def test_records_endpoint_supports_limit_and_not_found(monkeypatch):
    records = [{"id": 1, "topic": "Portability"}, {"id": 2, "topic": "Renewal"}]
    monkeypatch.setattr(main, "RECORDS", records)

    assert client.get("/records?limit=1").json() == records[:1]
    assert client.get("/records/99").status_code == 404


def test_search_endpoint_returns_ranked_matches(monkeypatch):
    records = [
        {
            "id": 1,
            "topic": "Portability",
            "insurance_type": "Health",
            "rule_summary": "Move your health policy at renewal",
            "time_limit": "45 to 60 days",
            "who_to_contact": "New insurer",
            "source_url": "https://example.test/portability",
        }
    ]
    monkeypatch.setattr(main, "RECORDS", records)

    response = client.get("/search", params={"q": "health policy portability"})

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == 1


def test_ask_uses_fake_llm_and_returns_valid_citation(monkeypatch):
    from app import rag

    hit = {
        "title": "Free-look period",
        "slug": "free-look-period",
        "source": "https://example.test/free-look",
        "page": 1,
        "score": 0.9,
        "text": "You can return the policy during the free-look period.",
    }
    monkeypatch.setattr(rag, "retrieve", lambda question, max_chars, top_k: [hit])
    monkeypatch.setattr(
        rag,
        "call_llm",
        lambda system, user: (
            '{"answer":"You can return it during the free-look period.",'
            '"answerable":true,"citations":["S1"],"confidence":"high"}'
        ),
    )

    response = client.post("/ask", json={"question": "Can I return my policy?"})

    assert response.status_code == 200
    result = response.json()
    assert result["answerable"] is True
    assert result["citations"][0]["source"] == hit["source"]
    assert "disclaimer" in result


def test_agent_endpoint_returns_agent_result(monkeypatch):
    from app import graph

    monkeypatch.setattr(graph, "is_waiting", lambda thread_id: False)
    monkeypatch.setattr(
        graph,
        "start",
        lambda question, thread_id: {
            "status": "done",
            "thread_id": thread_id,
            "answer": question,
        },
    )

    response = client.post("/agent", json={"question": "What is portability?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "What is portability?"

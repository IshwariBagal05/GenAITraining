from typing import Literal,Optional

from app.chat import answer_question
from app.llm import LLMError
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.records import load_records, get_by_id
from app.smart_search import rank

DISCLAIMER = ("Information from IRDAI's official consumer pages, not legal or "
              "financial advice. Check your policy document and contact your "
              "insurer or the Insurance Ombudsman for your case.")

app = FastAPI(title="InsureClear API", version="0.1.0")

RECORDS = load_records()


class Question(BaseModel):
    name: Optional[str] = None
    question: str = Field(..., min_length=3)


@app.get("/health")
def health():
    return {"status": "ok", "records_loaded": len(RECORDS)}


@app.get("/records")
def list_records(limit: Optional[int] = Query(None, ge=1, le=100)):
    return RECORDS[:limit] if limit else RECORDS


@app.get("/records/{record_id}")
def read_record(record_id: int):
    record = get_by_id(RECORDS, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found")
    return record


@app.get("/search")
def search_records(q: str = Query(..., min_length=1)):
    results = rank(RECORDS, q)
    return {"query": q, "count": len(results), "results": results}


@app.post("/questions")
def ask_question(body: Question):
    matches = rank(RECORDS, body.question, top_k=3)
    if not matches:
        return {
            "question": body.question,
            "answer": "I could not find a matching rule in the IRDAI consumer pages I have.",
            "sources": [],
            "disclaimer": DISCLAIMER,
        }
    best = matches[0]
    return {
        "question": body.question,
        "answer": f"{best['topic']}: {best['rule_summary']} "
                  f"Time limit: {best['time_limit']}. Contact: {best['who_to_contact']}.",
        "sources": [{"topic": m["topic"], "source_url": m["source_url"],
                     "score": m["score"]} for m in matches],
        "disclaimer": DISCLAIMER,
    }

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3)
    prompt_version: Literal["v1", "v2"] = "v2"


class ChatResponse(BaseModel):
    answer: str
    confidence: Literal["low", "medium", "high"]
    follow_up: str
    sources: list[dict] = []
    disclaimer: str


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    try:
        result = answer_question(body.question, body.prompt_version)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {**result, "disclaimer": DISCLAIMER}

@app.get("/search/semantic")
def semantic_search(q: str = Query(..., min_length=2),
                    limit: int = Query(3, ge=1, le=10)):
    try:
        from app.vectorstore import query as semantic_query
        hits = semantic_query(q, limit)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Semantic index unavailable: {e}. Run: python -m app.vectorstore",
        )
    return {"query": q, "count": len(hits), "results": hits}
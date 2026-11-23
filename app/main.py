
import logging
import time
import uuid
from functools import lru_cache
from typing import Literal, Optional

from app.chat import answer_question
from app.llm import LLMError
from app.records import get_by_id, load_records
from app.smart_search import rank
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

DISCLAIMER = (
    "Information from IRDAI's official consumer pages, not legal or "
    "financial advice. Check your policy document and contact your "
    "insurer or the Insurance Ombudsman for your case."
)

app = FastAPI(title="InsureClear API", version="0.1.0")

RECORDS = load_records()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def cached_answer(question: str, prompt_version: str):
    return answer_question(question, prompt_version)


class Question(BaseModel):
    name: Optional[str] = None
    question: str = Field(..., min_length=3, max_length=2000)



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
    question: str = Field(..., min_length=3, max_length=2000)
    prompt_version: Literal["v1", "v2"] = "v2"


class ChatResponse(BaseModel):
    answer: str
    confidence: Literal["low", "medium", "high"]
    follow_up: str
    sources: list[dict] = []
    disclaimer: str


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    start_time = time.perf_counter()

    try:
        result = cached_answer(body.question.strip(), body.prompt_version)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
        "Chat request completed | latency_ms=%s | cache=%s",
        latency_ms,
        cached_answer.cache_info(),
    )

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

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


@app.post("/ask")
def ask_endpoint(body: AskRequest):
    try:
        from app.rag import ask as rag_ask
        result = rag_ask(body.question)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"RAG unavailable: {e}")
    return {**result, "disclaimer": DISCLAIMER}

class AgentRequest(BaseModel):
    thread_id: Optional[str] = None
    question: Optional[str] = Field(None, min_length=3, max_length=2000)
    approve: Optional[bool] = None
    args: Optional[dict] = None


@app.post("/agent")
def agent_endpoint(body: AgentRequest):
    try:
        from app import graph as agent_graph
        waiting = bool(body.thread_id) and agent_graph.is_waiting(body.thread_id)

        if waiting and body.approve is not None:        # resume a paused thread
            result = agent_graph.resume(body.thread_id, body.approve, body.args)
        elif waiting:
            raise HTTPException(status_code=409,
                                detail="This thread is waiting for approval. "
                                       "Send approve true or false first.")
        elif body.question:                              # new question or follow-up
            thread_id = body.thread_id or str(uuid.uuid4())
            result = agent_graph.start(body.question, thread_id)
        elif body.approve is not None:
            raise HTTPException(status_code=409,
                                detail="No approval is pending for this thread_id.")
        else:
            raise HTTPException(status_code=422,
                                detail="Send a question, or approve with a thread_id.")
    except HTTPException:
        raise
    return result
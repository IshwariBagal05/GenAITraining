import html
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))          # lets "from app..." work under `streamlit run`

from app.timeline import POLICY_TYPES, build_timeline   # noqa: E402
from app.tools import FREE_LOOK_DAYS                    # noqa: E402

FEEDBACK_FILE = ROOT / "data" / "feedback.jsonl"
DEFAULT_API = os.getenv("INSURECLEAR_API_URL", "http://127.0.0.1:8000")
DISCLAIMER = ("Information from IRDAI's official consumer pages, not legal or financial "
              "advice. Check your policy document and contact your insurer or the "
              "Insurance Ombudsman for your case.")
SOLD_LABELS = {"offline": "Offline (in person or agent)",
               "electronic": "Electronic (bought online)",
               "distance": "Distance (phone or post)"}
EXAMPLES = [
    "I got my LIC policy by post 10 days back and I don't like it. Can I return it and get my money back?",
    "Insurance company rejected my claim because I informed them 3 days late. Is that allowed?",
    "What is portability in health insurance and can I keep my waiting period benefit?",
    "I bought a policy online on 20 October 2026. Till which date can I cancel it under free-look, and how much refund will I get on a 18500 premium?",
    "My hospital claim was rejected and the company is not replying. What are the steps to complain, and when can I go to the Insurance Ombudsman?",
    "Which health insurance company has the best claim settlement ratio in Maharashtra this year?",
]

TIMELINE_CSS = """<style>
.tl-strip{display:flex;gap:10px;flex-wrap:wrap}
.tl-step{flex:1 1 170px;border:1px solid rgba(128,128,128,.4);border-radius:10px;padding:10px 12px}
.tl-dot{width:24px;height:24px;border-radius:50%;background:#2e7d6b;color:#fff;font-size:13px;display:flex;align-items:center;justify-content:center;margin-bottom:6px}
.tl-label{font-weight:600}
.tl-day{font-size:1.1rem;font-weight:700;margin:2px 0}
.tl-when{opacity:.7;font-size:.8rem}
.tl-detail{font-size:.82rem;margin:6px 0;opacity:.9}
.tl-src{font-size:.78rem}
.tl-src a{display:block}
.tl-warn{font-size:.78rem;color:#b26a00;margin-top:4px}
</style>"""


class ApiError(Exception):
    pass


# ---------- API ----------
def post(api, path, payload, timeout):
    try:
        r = requests.post(f"{api}{path}", json=payload, timeout=timeout)
    except requests.exceptions.ConnectionError:
        raise ApiError(f"Cannot reach the API at {api}. Start it in another terminal: "
                       "uvicorn app.main:app --reload")
    except requests.exceptions.Timeout:
        raise ApiError("The API took too long to answer. Try again in a minute.")
    if r.status_code != 200:
        try:
            detail = r.json().get("detail", r.text)
        except ValueError:
            detail = r.text
        raise ApiError(f"API error {r.status_code}: {detail}")
    return r.json()


def to_message(result, mode, question):
    msg = {"role": "assistant", "content": result.get("answer", ""), "mode": mode,
           "question": question, "rating": None,
           "confidence": result.get("confidence"), "answerable": result.get("answerable"),
           "thread_id": result.get("thread_id")}
    if mode == "Ask":
        msg["sources"] = [{"title": c["title"], "source": c["source"], "page": c.get("page"),
                           "snippet": c.get("snippet", "")} for c in result.get("citations", [])]
    else:
        msg["sources"] = [{"title": s["title"], "source": s["source"]}
                          for s in result.get("sources_consulted", [])]
        msg["trace"] = result.get("trace", [])
    return msg


def handle_agent_result(result, question):
    st.session_state.thread_id = result.get("thread_id", st.session_state.thread_id)
    if result.get("status") == "needs_approval":
        st.session_state.pending = {"thread_id": result["thread_id"],
                                    "approval": result["approval"], "question": question}
    else:
        st.session_state.pending = None
        st.session_state.messages.append(to_message(result, "Agent", question))


# ---------- feedback ----------
def save_feedback(msg, rating):
    FEEDBACK_FILE.parent.mkdir(exist_ok=True)
    row = {"time": datetime.now().isoformat(timespec="seconds"), "rating": rating,
           "mode": msg.get("mode"), "question": msg.get("question"),
           "answer": msg.get("content"), "confidence": msg.get("confidence"),
           "answerable": msg.get("answerable"), "thread_id": msg.get("thread_id"),
           "sources": [s.get("source") for s in msg.get("sources") or []]}
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def feedback_counts():
    up = down = 0
    if FEEDBACK_FILE.exists():
        for line in FEEDBACK_FILE.read_text(encoding="utf-8").splitlines():
            try:
                rating = json.loads(line).get("rating")
            except ValueError:
                continue
            up += rating == "up"
            down += rating == "down"
    return up, down


# ---------- rendering ----------
def timeline_html(steps):
    cards = []
    for i, s in enumerate(steps, start=1):
        links = "".join(
            f'<a href="{html.escape(src["url"])}" target="_blank">'
            f'{"✅" if src["found"] else "⚠️"} {html.escape(src["slug"].replace("-", " ").title())}</a>'
            for src in s["sources_checked"])
        when = f'<div class="tl-when">{html.escape(s["date"])}</div>' if s.get("date") else ""
        warn = ('<div class="tl-warn">This day count was not found in the page text. '
                'Check the page.</div>') if s.get("days_on_page") is False else ""
        cards.append(
            '<div class="tl-step">'
            f'<div class="tl-dot">{i}</div>'
            f'<div class="tl-label">{html.escape(s["label"])}</div>'
            f'<div class="tl-day">{html.escape(s["day_text"])}</div>{when}'
            f'<div class="tl-detail">{html.escape(s["detail"])}</div>'
            f'<div class="tl-src">{links}</div>{warn}</div>')
    return TIMELINE_CSS + '<div class="tl-strip">' + "".join(cards) + "</div>"


def render_extras(m):
    bits = [f"Mode: {m['mode']}"]
    if m.get("confidence"):
        bits.append(f"Confidence: {m['confidence']}")
    if m.get("answerable") is False:
        bits.append("Not covered by the IRDAI pages I have")
    st.caption(" · ".join(bits))

    sources = m.get("sources") or []
    if sources:
        with st.expander(f"Sources ({len(sources)})"):
            for s in sources:
                line = f"**[{s['title']}]({s['source']})**" if s.get("source") else f"**{s['title']}**"
                if s.get("page"):
                    line += f" · page {s['page']}"
                st.markdown(line)
                if s.get("snippet"):
                    st.caption(s["snippet"] + "…")
    if m.get("trace"):
        with st.expander("What the agent did"):
            for t in m["trace"]:
                st.markdown(f"Step {t['step']}: `{t['tool']}` ({'ok' if t['ok'] else 'failed'})")
                st.code(json.dumps(t["args"], ensure_ascii=False), language="json")


def render_feedback(i, m):
    if m.get("rating"):
        st.caption(f"Thanks, your {'👍' if m['rating'] == 'up' else '👎'} was saved.")
        return
    c1, c2, _ = st.columns([1, 1, 10])
    if c1.button("👍", key=f"up_{i}"):
        save_feedback(m, "up")
        m["rating"] = "up"
        st.rerun()
    if c2.button("👎", key=f"down_{i}"):
        save_feedback(m, "down")
        m["rating"] = "down"
        st.rerun()


# ---------- page ----------
st.set_page_config(page_title="InsureClear", page_icon="🛡️", layout="wide")
for key, default in {"messages": [], "pending": None, "thread_id": None}.items():
    st.session_state.setdefault(key, default)

with st.sidebar:
    st.header("Settings")
    mode = st.radio("Mode", ["Ask", "Agent"],
                    help="Ask answers from the IRDAI pages with citations. Agent can also run "
                         "the free-look refund calculator, and asks you to approve first.")
    api = st.text_input("API address", DEFAULT_API)

    st.header("Your policy")
    ptype = st.radio("Policy type", POLICY_TYPES, format_func=str.capitalize, horizontal=True)
    sold_via = st.selectbox("How was it sold?", list(FREE_LOOK_DAYS),
                            format_func=SOLD_LABELS.get, disabled=(ptype == "motor"))
    received = st.date_input("Date the policy was received", value=date.today())

    st.header("Try an example")
    example = st.selectbox("Question", EXAMPLES, label_visibility="collapsed")
    if st.button("Ask this question"):
        st.session_state.queued = example
    if st.button("New conversation"):
        st.session_state.messages, st.session_state.pending, st.session_state.thread_id = [], None, None
        st.rerun()
    up, down = feedback_counts()
    st.caption(f"Feedback saved: 👍 {up} · 👎 {down}")

st.title("🛡️ InsureClear")
st.caption(DISCLAIMER)

with st.expander("📅 Your rights timeline", expanded=True):
    try:
        steps = build_timeline(ptype, sold_via, received)
        st.markdown(timeline_html(steps), unsafe_allow_html=True)
        st.caption("✅ the quoted fact was found in the downloaded IRDAI page. "
                   "⚠️ it was not found, so check the page. Where a page gives no day "
                   "count, none is shown. Day counts for the free-look step come from the "
                   "same rules as the refund calculator.")
    except (OSError, ValueError, KeyError) as e:
        st.error(f"Could not build the timeline: {e}")

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant" and "mode" in m:
            render_extras(m)
            render_feedback(i, m)

pending = st.session_state.pending
if pending:
    args = pending["approval"].get("args") or {}
    original = json.dumps(args, indent=2, ensure_ascii=False)
    with st.chat_message("assistant"):
        st.warning("Before I calculate, please check these values. I read them from your message.")
        st.markdown(f"Tool: `{pending['approval'].get('tool')}`")
        edited = st.text_area("Values (edit them if something is wrong)", value=original,
                              height=180, key=f"args_{pending['thread_id']}_{len(st.session_state.messages)}")
        c1, c2, _ = st.columns([1, 1, 6])
        approve = c1.button("✅ Approve", key="approve_btn")
        reject = c2.button("❌ Reject", key="reject_btn")
    if approve or reject:
        payload = {"thread_id": pending["thread_id"], "approve": bool(approve)}
        if approve and edited.strip() != original.strip():
            try:
                override = json.loads(edited)
            except ValueError:
                st.error("The values are not valid JSON.")
                st.stop()
            if isinstance(override, dict) and override:
                payload["args"] = override
        try:
            with st.spinner("Working..."):
                result = post(api, "/agent", payload, 180)
        except ApiError as e:
            st.error(str(e))
            st.stop()
        handle_agent_result(result, pending["question"])
        st.rerun()

queued = st.session_state.pop("queued", None)
prompt = st.chat_input("Ask about your insurance rights...", disabled=bool(pending))
if not prompt and queued and not pending:
    prompt = queued

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    try:
        with st.spinner("Searching the IRDAI pages..."):
            if mode == "Ask":
                result = post(api, "/ask", {"question": prompt}, 120)
                st.session_state.messages.append(to_message(result, "Ask", prompt))
            else:
                payload = {"question": prompt}
                if st.session_state.thread_id:
                    payload["thread_id"] = st.session_state.thread_id
                handle_agent_result(post(api, "/agent", payload, 180), prompt)
    except ApiError as e:
        st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {e}"})
    st.rerun()
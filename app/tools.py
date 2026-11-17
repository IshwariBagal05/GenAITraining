import inspect
from datetime import date, datetime, timedelta

# Days allowed to return a policy, by how it was sold.
# CHECK these against the free-look page (command in Job 2) and edit them if it says otherwise.
FREE_LOOK_DAYS = {"offline": 15, "electronic": 30, "distance": 30}

HIDDEN_ARGS = {"today"}      # arguments the model is not allowed to set


def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Date must look like 2026-10-20 (YYYY-MM-DD), got '{value}'")


def _money(name, value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number, got '{value}'")
    if number < 0:
        raise ValueError(f"{name} cannot be negative")
    return number


def free_look_calculator(received_date, sold_via, premium, medical_exam_cost=0,
                         stamp_duty=0, proportionate_risk_premium=0, today=None):
    """Last date to return a policy and the estimated refund."""
    sold_via = str(sold_via).strip().lower()
    if sold_via not in FREE_LOOK_DAYS:
        raise ValueError(f"sold_via must be one of: {', '.join(FREE_LOOK_DAYS)}; got '{sold_via}'")

    received = _to_date(received_date)
    premium = _money("premium", premium)
    if premium <= 0:
        raise ValueError("premium must be greater than 0")
    medical = _money("medical_exam_cost", medical_exam_cost)
    stamp = _money("stamp_duty", stamp_duty)
    risk = _money("proportionate_risk_premium", proportionate_risk_premium)

    days = FREE_LOOK_DAYS[sold_via]
    last_date = received + timedelta(days=days)
    today_date = _to_date(today) if today else date.today()
    days_left = (last_date - today_date).days

    deductions = {"proportionate_risk_premium": round(risk, 2),
                  "medical_exam_cost": round(medical, 2),
                  "stamp_duty": round(stamp, 2)}
    total = round(risk + medical + stamp, 2)
    refund = max(0.0, round(premium - total, 2))

    assumptions = [
        f"The day the policy was received is day 0, so the last day is received date + {days} days "
        f"for a {sold_via} sale.",
        "Refund = premium minus proportionate risk premium, medical examination cost and stamp duty.",
        "Unit-linked policies (ULIPs) can follow different refund rules and are not handled here.",
        "This is an estimate. Confirm the day count and the deductions with your insurer.",
    ]
    if risk == 0:
        assumptions.insert(2, "No proportionate risk premium was given, so none is deducted. "
                              "The insurer's real figure will lower the refund.")
    if received > today_date:
        assumptions.append("The received date is in the future. Check it.")

    return {
        "received_date": received.isoformat(),
        "sold_via": sold_via,
        "days_allowed": days,
        "last_date": last_date.isoformat(),
        "within_window": days_left >= 0,
        "days_left": days_left,
        "premium": round(premium, 2),
        "deductions": deductions,
        "total_deductions": total,
        "estimated_refund": refund,
        "assumptions": assumptions,
    }


def rag_search(query, top_k=3):
    """Search the IRDAI pages and return the closest text chunks."""
    from app.rag import DEFAULT_CONFIG, retrieve   # imported here so tests need no model
    top_k = max(1, min(int(top_k), 5))
    hits = retrieve(str(query), DEFAULT_CONFIG["max_chars"], top_k)
    return [{"title": h["title"], "source": h["source"], "page": h["page"],
             "score": h["score"], "text": h["text"]} for h in hits]


TOOLS = {
    "rag_search": {
        "fn": rag_search,
        "signature": "rag_search(query)",
        "doc": "Search the IRDAI policyholder pages. Returns up to 3 text chunks with their "
               "topic titles. Use it for any question about rules, limits or procedures.",
    },
    "free_look_calculator": {
        "fn": free_look_calculator,
        "signature": "free_look_calculator(received_date, sold_via, premium, "
                     "medical_exam_cost, stamp_duty, proportionate_risk_premium)",
        "doc": "Returns the last date to return a policy and the estimated refund. "
               "received_date is YYYY-MM-DD, the day the policy document was received. "
               "sold_via is 'offline' (in person or through an agent), 'electronic' "
               "(bought online) or 'distance' (phone, post or other non face-to-face sale). "
               "premium is a number. The last three are numbers and optional (default 0).",
    },
}


def describe_tools():
    return "\n".join(f"- {t['signature']}: {t['doc']}" for t in TOOLS.values())


def call_tool(name, args):
    """Run a tool safely. Always returns {"ok": True, "result": ...} or {"ok": False, "error": ...}."""
    tool = TOOLS.get(name)
    if tool is None:
        return {"ok": False, "error": f"Unknown tool '{name}'. Available: {', '.join(TOOLS)}"}
    if not isinstance(args, dict):
        return {"ok": False, "error": "args must be a JSON object"}
    allowed = set(inspect.signature(tool["fn"]).parameters) - HIDDEN_ARGS
    unknown = set(args) - allowed
    if unknown:
        return {"ok": False, "error": f"Unknown argument(s): {', '.join(sorted(unknown))}. "
                                      f"Allowed: {', '.join(sorted(allowed))}"}
    try:
        return {"ok": True, "result": tool["fn"](**args)}
    except (ValueError, TypeError) as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"Tool failed: {e}"}
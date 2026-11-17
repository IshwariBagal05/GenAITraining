import json
import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

try:
    from langgraph.checkpoint.memory import InMemorySaver as Saver
except ImportError:                                   # older versions
    from langgraph.checkpoint.memory import MemorySaver as Saver

from app.agent_loop import (GIVE_UP, MAX_STEPS, decide, finalize,
                            observation_text, sources_from)
from app.tools import call_tool

APPROVAL_TOOLS = {"free_look_calculator"}      # tools that need a human OK first


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]    # conversation memory: new messages are appended
    decision: dict
    steps: int
    trace: list
    sources: list
    answer: dict


def think(state: AgentState):
    """Ask the model what to do next."""
    messages = list(state["messages"])
    for _ in range(3):
        decision = decide(messages)
        if decision.get("action") in ("tool", "final"):
            return {"decision": decision}
        messages.append({"role": "user", "content":
                         "Your last reply was not a valid JSON object. Reply with one JSON object."})
    return {"decision": {"action": "give_up"}}


def route_after_think(state: AgentState):
    action = state["decision"].get("action")
    if action != "tool" or state["steps"] >= MAX_STEPS:
        return "finish"
    if state["decision"].get("tool") in APPROVAL_TOOLS:
        return "approve"
    return "run_tool"


def approve(state: AgentState) -> Command[Literal["run_tool", "think"]]:
    """The one approval step. Only interrupt() happens here, because this node
    restarts from its first line when the graph is resumed."""
    d = state["decision"]
    reply = interrupt({
        "type": "approval_needed",
        "tool": d.get("tool"),
        "args": d.get("args"),
        "message": "The agent wants to run this tool with these values. Check them, "
                   "then approve, edit the args, or reject.",
    })
    reply = reply if isinstance(reply, dict) else {}

    if reply.get("approve") is True:
        new_args = reply.get("args")
        if isinstance(new_args, dict) and new_args:    # only a non-empty dict counts as a correction                 
            return Command(update={"decision": {**d, "args": new_args}}, goto="run_tool")
        return Command(goto="run_tool")

    return Command(
        update={"messages": [
                    {"role": "assistant", "content": json.dumps(d, ensure_ascii=False)},
                    {"role": "tool", "content": json.dumps(
                        {"ok": False, "error": "The user did not approve this calculation. "
                                               "Ask them to confirm the details."})}],
                "steps": state["steps"] + 1},
        goto="think",
    )


def run_tool(state: AgentState):
    d = state["decision"]
    name, args = d.get("tool"), d.get("args") or {}
    observation = call_tool(name, args)
    return {
        "messages": [{"role": "assistant", "content": json.dumps(d, ensure_ascii=False)},
                     {"role": "tool", "content": observation_text(observation)}],
        "steps": state["steps"] + 1,
        "trace": state["trace"] + [{"step": state["steps"] + 1, "tool": name,
                                    "args": args, "ok": observation["ok"]}],
        "sources": state["sources"] + sources_from(name, observation),
    }


def finish(state: AgentState):
    d = state["decision"]
    if d.get("action") == "final":
        answer = finalize(d, any(t["ok"] for t in state["trace"]), state["sources"])
    else:
        answer = {"answer": GIVE_UP, "answerable": False, "confidence": "low",
                  "sources_consulted": []}
    return {"answer": answer,
            "messages": [{"role": "assistant", "content": answer["answer"]}]}


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("think", think)
    g.add_node("approve", approve)
    g.add_node("run_tool", run_tool)
    g.add_node("finish", finish)
    g.add_edge(START, "think")
    g.add_conditional_edges("think", route_after_think, ["approve", "run_tool", "finish"])
    g.add_edge("run_tool", "think")
    g.add_edge("finish", END)
    return g.compile(checkpointer=Saver())          # the checkpointer is the memory


GRAPH = build_graph()


def _config(thread_id):
    return {"configurable": {"thread_id": thread_id}}


def is_waiting(thread_id):
    """True if this thread is paused at the approval step."""
    return bool(GRAPH.get_state(_config(thread_id)).next)


def _package(result, thread_id):
    if result.get("__interrupt__"):
        return {"status": "needs_approval", "thread_id": thread_id,
                "approval": result["__interrupt__"][0].value}
    return {"status": "done", "thread_id": thread_id, **result["answer"],
            "trace": result["trace"]}


def start(question, thread_id):
    first = {"messages": [{"role": "user", "content": question}], "decision": {},
             "steps": 0, "trace": [], "sources": [], "answer": {}}
    return _package(GRAPH.invoke(first, _config(thread_id)), thread_id)


def resume(thread_id, approve_flag, args=None):
    reply = {"approve": bool(approve_flag), "args": args}
    return _package(GRAPH.invoke(Command(resume=reply), _config(thread_id)), thread_id)
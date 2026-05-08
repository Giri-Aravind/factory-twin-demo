"""LangGraph supervisor — nodes, edges, routing.

Multi-step query flow:

  intent (is_multi_step?) -> decompose -> start_step -> precheck -> select -> params
                                                                              -> sql -> execute -> collect
                                                                              -> respond -> complete_step -> END (await user)

Single-step flow:

  intent -> precheck -> select -> params -> sql -> execute -> collect -> respond -> END

Continue-plan flow (user said "yes" to continue):

  intent (continue_plan) -> start_step -> precheck -> ... -> respond -> complete_step -> END

NOTE: precheck does a lightweight ambiguity check (very short queries
with no action verb) and otherwise passes through. The Demand/Supply
category classifier was removed in v7 — it was being used as a hard
filter on vector search, and a single misclassification excluded the
correct endpoint with no recovery path. Endpoint selection now searches
across all 10 endpoints and the reranker handles disambiguation.
"""
import json
import os
from groq import Groq
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from agents.state import WorkflowState
from agents.intent_detector import detect_intent
from agents.endpoint_selector import select_endpoint
from agents.parameter_extractor import extract
from agents.sql_generator import generate_variables
from agents.response_generator import generate_response
from agents.query_decomposer import decompose_query
from agents.plan_manager import start_step, complete_step
from scripts.graphql import graphql
from agents import pipeline_tracker as tracker

load_dotenv()


# ─── Nodes ───────────────────────────────────────────────────────────────────

def intent_node(state):
    print("  -> intent")
    tracker.emit("Intent Detection", "Classifying query intent")
    return detect_intent(state)


def decompose_node(state):
    print("  -> decompose")
    tracker.emit("Query Decomposer", "Breaking into multi-step plan")
    return decompose_query(state)


def start_step_node(state):
    print("  -> start_step")
    plan = state.get("query_plan", {})
    step_num = plan.get("current_step", "?") if plan else "?"
    tracker.emit("Plan Manager", f"Starting step {step_num}")
    return start_step(state)


def complete_step_node(state):
    print("  -> complete_step")
    tracker.emit("Plan Manager", "Completing step")
    return complete_step(state)


def precheck_node(state):
    print("  -> precheck")
    tracker.emit("Pre-check", "Validating query clarity")
    q = state["user_query"].lower()
    actions = ["show", "display", "get", "list", "what", "how", "compare", "give", "find", "identify"]
    in_plan = bool(state.get("query_plan"))
    if (
        not in_plan
        and len(q.split()) <= 3
        and not any(a in q for a in actions)
        and not state.get("conversation_history")
    ):
        return {
            "needs_clarification": True,
            "clarification_question": (
                f'I see you mentioned "{state["user_query"]}". '
                "What would you like to know? I can show demand, supply, shortages, or purchase orders."
            ),
        }
    return {}


def select_node(state):
    print("  -> select")
    tracker.emit("Endpoint Selector", "Finding best endpoint via vector search + LLM rerank")
    return select_endpoint(state)


def params_node(state):
    """Run the parameter extractor on the current query for the chosen endpoint.

    The extractor returns three sibling lists:
      - resolved_variables: GraphQL var name -> value (LLM filled directly)
      - lookups_needed:     [{variable, table, lookup_value, return_as}, ...]
                            (SQL agent will resolve to UUIDs)
      - missing_required:   list of slot names that have no default and no
                            user-supplied value. When non-empty, supervisor
                            routes to ask_user.

    Special case: when clarification_response_node pre-populated the lookup
    (because the user answered a previous "I couldn't find X" prompt), we skip
    extraction entirely. The user's reply is already slotted into lookups_needed.
    """
    # Clarification resume — params already pre-populated, just pass through
    if state.get("_clarification_resume"):
        ep = state.get("current_endpoint", {})
        ep_name = ep.get("endpoint_name", "?")
        print(f"  -> params ({ep_name}) [resume — skipping extraction]")
        return {
            # Keep the values clarification_response_node set
            "resolved_variables": state.get("resolved_variables") or {},
            "lookups_needed": state.get("lookups_needed") or [],
            "missing_required": state.get("missing_required") or [],
            # Clear the flag so subsequent turns don't keep skipping
            "_clarification_resume": False,
            "graphql_variables": None,
            "graphql_result": None,
            "graphql_error": None,
            "unresolved_entities": None,
            "graphql_resolution_errors": None,
        }

    ep = state.get("current_endpoint", {})
    ep_name = ep.get("endpoint_name", "?")
    print(f"  -> params ({ep_name})")
    tracker.emit("Parameter Extractor", f"Extracting parameters for {ep_name}")

    user_query = state["user_query"]
    result = extract(user_query, ep_name)

    if result.get("error"):
        print(f"  [Params] ERROR: {result['error']}")

    return {
        "resolved_variables": result.get("resolved_variables", {}),
        "lookups_needed": result.get("lookups_needed", []),
        "missing_required": result.get("missing_required", []),
        # Reset graphql state from any prior endpoint in this turn
        "graphql_variables": None,
        "graphql_result": None,
        "graphql_error": None,
        # Reset SQL agent's failure flags too — about to re-run sql_node
        "unresolved_entities": None,
        "graphql_resolution_errors": None,
    }


def sql_node(state):
    print("  -> sql_generator")
    ep_name = (state.get("current_endpoint") or {}).get("endpoint_name", "?")
    tracker.emit("SQL Generator", f"Resolving entity names and building variables for {ep_name}")
    return generate_variables(state)


def execute_node(state):
    ep = state.get("current_endpoint", {})
    ep_name = ep.get("endpoint_name", "?")
    variables = state.get("graphql_variables", {}) or {}
    print(f"  -> execute ({ep_name})")
    tracker.emit("GraphQL Execute", f"Fetching data from {ep_name}")

    try:
        result = graphql.execute(ep.get("query", ""), variables)
        data = graphql.extract_data(result, ep.get("response_path", []))
        # Log shape and emptiness so we can diagnose empty-response cases
        if isinstance(data, list):
            print(f"  [GraphQL] OK (type=list, len={len(data)})")
            if len(data) == 0:
                # Show the variables we sent — most empty results are caused
                # by overly-specific filters (date window, site, partGroup).
                clean_vars = {k: v for k, v in variables.items() if v is not None}
                print(f"  [GraphQL] EMPTY result — variables sent: {clean_vars}")
        elif isinstance(data, dict):
            print(f"  [GraphQL] OK (type=dict, keys={list(data.keys())[:6]})")
        else:
            print(f"  [GraphQL] OK (type={type(data).__name__})")
        return {"graphql_result": data, "graphql_error": None}
    except Exception as e:
        print(f"  [GraphQL] ERROR: {e}")
        return {"graphql_result": None, "graphql_error": str(e)}


def collect_node(state):
    ep = state.get("current_endpoint", {})
    print(f"  -> collect ({ep.get('endpoint_name', '?')})")

    accumulated = list(state.get("endpoint_results", []))
    accumulated.append({
        "endpoint_name": ep.get("endpoint_name"),
        "display_name": ep.get("display_name"),
        "chart_type": ep.get("chart_type"),
        "data": state.get("graphql_result"),
        "error": state.get("graphql_error"),
    })

    next_idx = state.get("current_endpoint_index", 0) + 1
    endpoints = state.get("selected_endpoints", [])
    next_ep = endpoints[next_idx] if next_idx < len(endpoints) else None

    return {
        "endpoint_results": accumulated,
        "current_endpoint_index": next_idx,
        "current_endpoint": next_ep,
        "graphql_variables": None,
        "graphql_result": None,
        "graphql_error": None,
        "parameters": None,
        "missing_params": None,
    }


def respond_node(state):
    print("  -> respond")
    tracker.emit("Response Generator", "Generating natural language response")
    return generate_response(state)


def follow_up_node(state):
    """Follow-ups are rewritten as new data queries.

    We do a small LLM call to rewrite the follow-up into a self-contained query
    using the conversation history, then route to precheck.
    """
    print("  -> follow_up (rewrite)")
    query = state["user_query"]
    history = state.get("conversation_history", [])
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content'][:300]}" for m in history[-8:]
    )

    system = (
        "You rewrite follow-up questions into self-contained queries.\n"
        "Use the conversation history to fill in pronouns and references.\n"
        "Return ONLY JSON with a 'rewritten_query' field. No explanations.\n\n"
        f"CONVERSATION:\n{history_text}"
    )

    try:
        api_key = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.getenv("LIGHTWEIGHT_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": query},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=512,
        )
        result = json.loads(resp.choices[0].message.content)
        rewritten = result.get("rewritten_query", query)
        print(f"  [FollowUp] Rewritten: {rewritten}")
        return {"user_query": rewritten, "intent": "new_data_query"}
    except Exception as e:
        print(f"  [FollowUp] Rewrite failed: {e}; using original query")
        return {"intent": "new_data_query"}


def clarification_response_node(state):
    """User answered a previous ask_user prompt. Resume deterministically.

    Reads `pending_clarification` to know:
      - which endpoint we were running
      - what field was missing
      - what the original query was
      - if the failure was a lookup miss, the table + variable + return_as

    Two resume strategies:

    1. Lookup miss (`unresolved_lookup` is set): Bypass the parameter
       extractor entirely. Slot the user's reply directly as the lookup
       value, route to sql_generator. This avoids the case where the
       extractor sees both the original bad name AND the new good name
       in a merged query and tries to look up both.

    2. Missing required field or generic clarification: Fall back to the
       merged-query approach — let the extractor see the full context and
       fill the slot itself.
    """
    pending = state.get("pending_clarification") or {}
    user_reply = state.get("user_query", "").strip()
    original = pending.get("original_query", "")
    ep_name = pending.get("endpoint_name")
    unresolved_lookup = pending.get("unresolved_lookup")

    print(f"  -> clarification_response (resume {ep_name})")

    # Re-load the endpoint that was waiting on us
    from schema.endpoint_schema import get_endpoint_by_name
    endpoint = get_endpoint_by_name(ep_name) if ep_name else None

    if not endpoint:
        # Couldn't find prior endpoint — fall back to treating as new query
        print(f"  [Clarification] No prior endpoint ({ep_name}); falling back")
        return {"intent": "new_data_query", "pending_clarification": None}

    # Strategy 1: lookup miss — slot reply directly, skip extractor.
    if unresolved_lookup and user_reply:
        # Strip common prefixes the user might add ("the part is X", "for X")
        cleaned = _strip_filler(user_reply)
        return_as = unresolved_lookup.get("return_as", "list")
        lookup_value = [cleaned] if return_as == "list" else cleaned

        new_lookup_entry = {
            "variable": unresolved_lookup.get("variable"),
            "table": unresolved_lookup.get("table"),
            "lookup_value": lookup_value,
            "return_as": return_as,
        }
        print(
            f"  [Clarification] Direct slot: "
            f"{new_lookup_entry['variable']} = {cleaned!r} "
            f"({unresolved_lookup.get('table')})"
        )

        return {
            "user_query": f"{original} | {cleaned}",  # for logging only
            "current_endpoint": endpoint,
            "selected_endpoints": [endpoint],
            "current_endpoint_index": 0,
            # Pre-populate params output so route from clarification_response
            # to params still works but params will pass through resolved data
            "resolved_variables": {},
            "lookups_needed": [new_lookup_entry],
            "missing_required": [],
            # Clear all UI/error flags
            "pending_clarification": None,
            "needs_clarification": False,
            "clarification_question": "",
            "unresolved_entities": None,
            "graphql_resolution_errors": None,
            "graphql_variables": None,
            "graphql_result": None,
            "graphql_error": None,
            # Signal to params_node that it can skip extraction
            "_clarification_resume": True,
        }

    # Strategy 2: missing-required (or generic) — merge queries, let extractor work
    if original and user_reply:
        merged_query = f"{original} {user_reply}"
    else:
        merged_query = user_reply or original

    print(f"  [Clarification] Merged query: {merged_query!r}")

    return {
        "user_query": merged_query,
        "current_endpoint": endpoint,
        "selected_endpoints": [endpoint],
        "current_endpoint_index": 0,
        # Clear the pending flag — we're handling it now
        "pending_clarification": None,
        # Reset clarification UI flags so we don't echo the prior question
        "needs_clarification": False,
        "clarification_question": "",
        # Clear stale resolution failures from prior turn — about to re-run
        "unresolved_entities": None,
        "graphql_resolution_errors": None,
        "resolved_variables": None,
        "lookups_needed": None,
        "missing_required": None,
        "graphql_variables": None,
        "graphql_result": None,
        "graphql_error": None,
    }


_FILLER_PREFIXES = (
    "the part is ", "the site is ", "the supplier is ", "the customer is ",
    "the process is ", "use ", "for ", "it is ", "it's ", "that's ",
)


def _strip_filler(reply: str) -> str:
    """Strip common conversational prefixes from a clarification reply.

    Examples:
      "the part is TDAU-6161-VHBH" -> "TDAU-6161-VHBH"
      "for Minneapolis"            -> "Minneapolis"
      "Lockheed Martin"            -> "Lockheed Martin" (unchanged)
    """
    s = reply.strip().rstrip(".!?")
    low = s.lower()
    for prefix in _FILLER_PREFIXES:
        if low.startswith(prefix):
            return s[len(prefix):].strip()
    return s


def general_chat_node(state):
    print("  -> general_chat")

    plan = state.get("query_plan")
    cleared_plan_msg = ""
    if plan:
        q = state["user_query"].lower().strip()
        if q in ("no", "stop", "cancel", "nevermind", "abort", "quit"):
            cleared_plan_msg = " I've cancelled the multi-step analysis."
            plan = None

    try:
        api_key = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.getenv("LIGHTWEIGHT_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {
                    "role": "system",
                    "content": "You are FactoryTwin AI. Respond briefly. Mention you help with demand, supply, purchase orders.",
                },
                {"role": "user", "content": state["user_query"]},
            ],
            temperature=0.5,
            max_tokens=512,
        )
        text = resp.choices[0].message.content.strip() + cleared_plan_msg
        return {"final_response": text, "chart_config": None, "query_plan": plan}
    except Exception:
        return {
            "final_response": "Hi! I can help with demand, supply, and purchase orders." + cleared_plan_msg,
            "chart_config": None,
            "query_plan": plan,
        }


def out_of_scope_node(state):
    print("  -> out_of_scope")
    return {
        "final_response": (
            "That's outside my scope. I help with manufacturing analytics — "
            "demand, supply, shortages, purchase orders."
        ),
        "chart_config": None,
    }


def ask_user_node(state):
    """Build a clarification question and emit pending_clarification.

    Three cases, in priority order:
      1. unresolved_entities — user named something the DB couldn't find.
         Ask them by name: "I couldn't find 'Boeing' as a supplier or customer..."
      2. missing_required — user didn't provide a required field.
         Ask by field: "To show X, I need: selectedMaterial..."
      3. fallback — generic prompt.

    All three set the same structured pending_clarification, which lets the
    next turn's clarification_response handler resume the endpoint cleanly
    once the user answers.
    """
    ep = state.get("current_endpoint", {})
    name = ep.get("display_name", "this analysis")

    unresolved = state.get("unresolved_entities") or []
    missing = state.get("missing_required") or state.get("missing_params") or []

    if unresolved:
        # Most-helpful path — name the failing entity directly.
        # If the user named multiple things, we list them all but treat the
        # first as the slot to fill on the resume.
        bad = unresolved[0]
        primary_name = bad.get("name", "the value you provided")
        label = bad.get("label", bad.get("table", "value"))

        if len(unresolved) == 1:
            q = (
                f"I couldn't find '{primary_name}' as a {label} in our records. "
                f"Could you double-check the name or provide a different one?"
            )
        else:
            names = ", ".join(f"'{e.get('name', '?')}'" for e in unresolved)
            q = (
                f"I couldn't find these in our records: {names}. "
                f"Could you double-check the names or provide alternatives?"
            )
        missing_field = bad.get("variable")
        # Carry enough lookup metadata that resume can bypass the extractor
        # and slot the user's reply directly. Without this we'd merge the
        # bad name + the new name into one query and the extractor might
        # try to look up both.
        unresolved_meta = {
            "table": bad.get("table"),
            "variable": bad.get("variable"),
            # Find return_as from endpoint schema
            "return_as": (
                ep.get("user_variables", {})
                .get(bad.get("variable"), {})
                .get("return_as", "list")
            ),
        }
    elif missing:
        q = f"To show {name}, I need: {', '.join(missing)}. Could you specify?"
        missing_field = missing[0]
        unresolved_meta = None
    else:
        q = state.get("clarification_question", "Could you provide more details?")
        missing_field = None
        unresolved_meta = None

    print(f"  -> ask_user: {q}")

    # Structured pending_clarification — carries everything we need to resume
    # cleanly when the user replies. The next turn's intent detector reads this
    # to know we're awaiting an answer; the clarification_response handler
    # uses it to slot the answer into the right endpoint without re-running
    # endpoint selection.
    pending = {
        "endpoint_name": ep.get("endpoint_name"),
        "missing_field": missing_field,
        "original_query": state.get("user_query", ""),
        "question_asked": q,
        # Only set when we asked because of unresolved_entities. When set,
        # the resume handler takes the user's reply as the literal value
        # for this lookup, bypassing the parameter extractor.
        "unresolved_lookup": unresolved_meta,
    }

    return {
        "needs_clarification": True,
        "clarification_question": q,
        "pending_clarification": pending,
    }


# ─── Routing ─────────────────────────────────────────────────────────────────

def route_intent(state):
    intent = state.get("intent", "new_data_query")

    if intent == "follow_up":
        return "follow_up"
    if intent == "clarification_response":
        return "clarification_response"
    if intent == "general_chat":
        return "general_chat"
    if intent == "out_of_scope":
        return "out_of_scope"
    if intent == "continue_plan":
        return "start_step"

    # new_data_query — check is_multi_step
    if state.get("is_multi_step"):
        return "decompose"
    return "precheck"


def route_decompose(state):
    """After decompose: if a plan was built, start step 1; otherwise normal flow."""
    if state.get("query_plan"):
        return "start_step"
    return "precheck"


def route_follow_up(state):
    return "precheck"


def route_precheck(state):
    if state.get("needs_clarification"):
        return "ask_user"
    return "select"


def route_select(state):
    if not state.get("selected_endpoints"):
        return "respond"
    return "params"


def route_params(state):
    """After parameter extraction, short-circuit to ask_user if a required
    slot has no value (selectedMaterial without a part name, etc.).
    Otherwise proceed to SQL."""
    if state.get("missing_required"):
        return "ask_user"
    return "sql"


def route_sql(state):
    """After SQL agent: route to ask_user if anything is unresolved.

    Two failure modes:
      - missing_required / missing_params: a slot has no value at all
      - unresolved_entities: the user named something but DB couldn't find it
        (e.g. "Boeing" as a supplier — silent fall-through used to send
        unfiltered data with confident wrong narrative)

    Both route to ask_user with a tailored question.
    """
    if state.get("missing_required") or state.get("missing_params"):
        return "ask_user"
    if state.get("unresolved_entities"):
        return "ask_user"
    return "execute"


def route_collect(state):
    idx = state.get("current_endpoint_index", 0)
    total = len(state.get("selected_endpoints", []))
    if idx < total:
        return "params"
    return "respond"


def route_respond(state):
    if state.get("query_plan"):
        return "complete_step"
    return "__end__"


# ─── Build graph ─────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(WorkflowState)

    g.add_node("intent", intent_node)
    g.add_node("decompose", decompose_node)
    g.add_node("start_step", start_step_node)
    g.add_node("complete_step", complete_step_node)
    g.add_node("precheck", precheck_node)
    g.add_node("select", select_node)
    g.add_node("params", params_node)
    g.add_node("sql", sql_node)
    g.add_node("execute", execute_node)
    g.add_node("collect", collect_node)
    g.add_node("respond", respond_node)
    g.add_node("follow_up", follow_up_node)
    g.add_node("clarification_response", clarification_response_node)
    g.add_node("general_chat", general_chat_node)
    g.add_node("out_of_scope", out_of_scope_node)
    g.add_node("ask_user", ask_user_node)

    g.add_edge(START, "intent")

    g.add_conditional_edges(
        "intent",
        route_intent,
        {
            "precheck": "precheck",
            "decompose": "decompose",
            "start_step": "start_step",
            "follow_up": "follow_up",
            "clarification_response": "clarification_response",
            "general_chat": "general_chat",
            "out_of_scope": "out_of_scope",
        },
    )

    g.add_conditional_edges(
        "decompose",
        route_decompose,
        {"start_step": "start_step", "precheck": "precheck"},
    )

    g.add_edge("start_step", "precheck")

    g.add_conditional_edges("follow_up", route_follow_up, {"precheck": "precheck"})

    # clarification_response loads the prior endpoint and resumes at params
    g.add_edge("clarification_response", "params")

    g.add_conditional_edges("precheck", route_precheck, {"ask_user": "ask_user", "select": "select"})
    g.add_conditional_edges("select", route_select, {"params": "params", "respond": "respond"})
    g.add_conditional_edges("params", route_params, {"sql": "sql", "ask_user": "ask_user"})
    g.add_conditional_edges("sql", route_sql, {"execute": "execute", "ask_user": "ask_user"})
    g.add_edge("execute", "collect")
    g.add_conditional_edges("collect", route_collect, {"params": "params", "respond": "respond"})

    g.add_conditional_edges("respond", route_respond, {"complete_step": "complete_step", "__end__": END})

    g.add_edge("complete_step", END)
    g.add_edge("general_chat", END)
    g.add_edge("out_of_scope", END)
    g.add_edge("ask_user", END)

    return g


compiled_graph = build_graph().compile()
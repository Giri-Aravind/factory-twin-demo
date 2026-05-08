"""Plan manager — progresses multi-step query plans.

Two functions:

1. start_step: prepares state to execute the current step (rewrites user_query
   to the step's standalone_query, sets category_hint, applies carry-forward).

2. complete_step: runs after respond_node — extracts entities from the result,
   marks the step complete, appends an LLM-generated "next step?" prompt.
"""
import json
import os

from dotenv import load_dotenv
from groq import Groq

from agents.entity_extractor import extract_entities

load_dotenv()


def _llm_transition_message(
    current_step: dict,
    next_step: dict | None,
    result_summary: str,
    total_steps: int,
) -> str:
    """Use LLM to generate a natural transition message between plan steps."""
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("LIGHTWEIGHT_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write brief, natural transition messages for a multi-step manufacturing analysis. "
                        "Return JSON: {\"message\": \"<1-2 sentence transition>\"}. "
                        "Be concise. Mention what was just found and what comes next."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "completed_step": current_step.get("description"),
                        "result_summary": result_summary[:300],
                        "next_step": next_step.get("description") if next_step else None,
                        "total_steps": total_steps,
                        "current_step_num": current_step.get("step_number"),
                    }),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=128,
        )
        result = json.loads(resp.choices[0].message.content)
        return result.get("message", "")
    except Exception as e:
        print(f"  [Plan/LLM] Transition message error: {e}")
        return ""


def start_step(state: dict) -> dict:
    """Prepare state for executing the current plan step."""
    plan = state.get("query_plan")
    if not plan:
        return {}

    current_num = plan.get("current_step", 1)
    step = next((s for s in plan["steps"] if s.get("step_number") == current_num), None)
    if not step:
        return {}

    standalone_query = step.get("standalone_query", "")

    # Resolve placeholders in the standalone_query using carry-forward
    resolved_query = _resolve_placeholders(standalone_query, plan, step)

    print(f"  [Plan] Starting step {current_num}: {step.get('description')}")
    print(f"  [Plan] Resolved query: {resolved_query}")

    update = {
        "user_query": resolved_query,
        "category": step.get("category_hint"),  # gives classifier a hint
        # Reset per-step fields so we don't carry stale data from a prior step
        "selected_endpoints": [],
        "current_endpoint_index": 0,
        "current_endpoint": None,
        "parameters": None,
        "missing_params": None,
        "graphql_variables": None,
        "graphql_result": None,
        "graphql_error": None,
        "endpoint_results": [],
        "final_response": None,
        "chart_config": None,
    }
    return update


def complete_step(state: dict) -> dict:
    """Mark the current step complete, extract entities, append next-step prompt."""
    plan = state.get("query_plan")
    if not plan:
        return {}

    current_num = plan.get("current_step", 1)
    steps = plan.get("steps", [])
    step = next((s for s in steps if s.get("step_number") == current_num), None)
    if not step:
        return {}

    # Extract entities from the step's result for carry-forward
    results = state.get("endpoint_results", [])
    entities = {}
    if results:
        r = results[0]
        entities = extract_entities(
            r.get("data"),
            r.get("chart_type", "table"),
            step.get("carry_forward", []),
        )

    # Mark step complete and store result info
    step["status"] = "complete"
    step["endpoint_used"] = results[0].get("endpoint_name") if results else None
    step["result_summary"] = (state.get("final_response") or "")[:200]
    step["result_entities"] = entities

    # Find next pending step whose dependencies are complete
    next_step = _find_next_executable_step(steps)

    response = state.get("final_response") or ""

    if next_step:
        plan["current_step"] = next_step["step_number"]
        transition = _llm_transition_message(step, next_step, step["result_summary"], len(steps))
        if not transition:
            transition = f"Next: {next_step['description']}."
        prompt = (
            f"\n\n**Step {current_num} of {len(steps)} complete.** "
            f"{transition} Want me to continue? (yes/no)"
        )
        final_response = response + prompt
    else:
        transition = _llm_transition_message(step, None, step["result_summary"], len(steps))
        if not transition:
            transition = ""
        prompt = f"\n\n*All {len(steps)} steps complete.* {transition}".rstrip()
        final_response = response + prompt

    print(f"  [Plan] Step {current_num} complete. Next: {next_step['step_number'] if next_step else 'DONE'}")

    return {
        "query_plan": plan,
        "final_response": final_response,
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _find_next_executable_step(steps: list) -> dict | None:
    """Find the next pending step whose dependencies are all complete."""
    for s in steps:
        if s.get("status") != "pending":
            continue
        deps = s.get("depends_on", [])
        if not deps:
            return s
        all_complete = all(
            any(p.get("step_number") == d and p.get("status") == "complete" for p in steps)
            for d in deps
        )
        if all_complete:
            return s
    return None


def _resolve_placeholders(query: str, plan: dict, current_step: dict) -> str:
    """Replace {customers_from_step_N}, {parts_from_step_N}, etc. with actual names.

    If the placeholder cannot be resolved, leave it in (the LLM downstream will see it).
    """
    if "{" not in query:
        return query

    steps = plan.get("steps", [])
    resolved = query

    for dep_num in current_step.get("depends_on", []):
        dep_step = next((s for s in steps if s.get("step_number") == dep_num), None)
        if not dep_step:
            continue
        entities = dep_step.get("result_entities") or {}

        for entity_type in ("customers", "parts", "suppliers", "sites"):
            placeholder = f"{{{entity_type}_from_step_{dep_num}}}"
            if placeholder in resolved:
                items = entities.get(entity_type) or []
                names = [x.get("name") for x in items if isinstance(x, dict) and x.get("name")]
                if names:
                    # Use top entity by default, or list of names
                    if len(names) == 1:
                        resolved = resolved.replace(placeholder, names[0])
                    else:
                        resolved = resolved.replace(placeholder, ", ".join(names[:5]))

    return resolved

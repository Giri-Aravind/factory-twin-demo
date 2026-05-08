"""Query decomposer — breaks multi-step queries into sequential steps."""
import json
import os
import uuid
from groq import Groq
from dotenv import load_dotenv
from schema.decomposer_schema import decomposer_system_prompt

load_dotenv()


MAX_STEPS = 5


def decompose_query(state: dict) -> dict:
    """Decompose a multi-step query into a structured plan.

    Returns a dict with `query_plan` populated, or sets is_multi_step=False
    if decomposition determines the query is not actually multi-step.
    """
    user_query = state.get("user_query", "")
    model = os.getenv("LIGHTWEIGHT_MODEL", "llama-3.1-8b-instant")
    api_key = os.getenv("GROQ_API_KEY")

    payload = json.dumps({"user_query": user_query}, indent=2)
    
    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": decomposer_system_prompt},
                {"role": "user", "content": payload},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            top_p=0.1,
            max_tokens=2048,
        )
        raw = response.choices[0].message.content
        result = json.loads(raw)
    except Exception as e:
        print(f"  [Decomposer] LLM error: {e}")
        return {"query_plan": None, "is_multi_step": False}

    is_multi_step = bool(result.get("is_multi_step"))
    raw_steps = result.get("steps") or []

    # Defensive checks: downgrade if not actually multi-step
    if not is_multi_step or not raw_steps:
        print("  [Decomposer] -> single-step (no decomposition needed)")
        return {"query_plan": None, "is_multi_step": False}

    if len(raw_steps) < 2:
        print("  [Decomposer] -> only 1 step returned, treating as single-step")
        return {"query_plan": None, "is_multi_step": False}

    if len(raw_steps) > MAX_STEPS:
        print(f"  [Decomposer] -> too many steps ({len(raw_steps)}), capping at {MAX_STEPS}")
        raw_steps = raw_steps[:MAX_STEPS]

    # Defensive: if no step has dependencies, this is parallel not sequential
    has_dependencies = any(s.get("depends_on") for s in raw_steps)
    if not has_dependencies:
        print("  [Decomposer] -> no dependencies between steps; treating as parallel multi-endpoint")
        return {"query_plan": None, "is_multi_step": False, "requires_multi_endpoint": True}

    # Build the plan
    steps = []
    for i, s in enumerate(raw_steps, start=1):
        step_number = s.get("step_number", i)
        steps.append({
            "step_number": step_number,
            "description": s.get("description", f"Step {step_number}"),
            "standalone_query": s.get("standalone_query", ""),
            "category_hint": s.get("category_hint"),
            "carry_forward": s.get("carry_forward", []),
            "depends_on": s.get("depends_on", []),
            "status": "pending",
            "endpoint_used": None,
            "result_summary": None,
            "result_entities": None,
        })

    plan = {
        "plan_id": str(uuid.uuid4()),
        "original_query": user_query,
        "steps": steps,
        "current_step": 1,
    }

    print(f"  [Decomposer] -> {len(steps)} steps planned")
    for s in steps:
        deps = f" (depends on {s['depends_on']})" if s["depends_on"] else ""
        print(f"    {s['step_number']}. {s['description']} [{s['category_hint']}]{deps}")

    return {
        "query_plan": plan,
        "is_multi_step": True,
        "requires_multi_endpoint": False,
    }

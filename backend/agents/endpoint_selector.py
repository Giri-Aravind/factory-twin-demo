"""Endpoint selector — vector search → LLM rerank → hydrate schema details.

Mirrors the standalone reranker setup:
- Vector DB returns top-K endpoint name + score (no full payload).
- ALWAYS calls the LLM reranker (no gap-skip optimization).
- If best vector score < min_score, returns nothing (low confidence).
- If reranker fails, falls back to vector top-1.

Schema details (query string, variables, response_path) are loaded
separately by name from endpoint_schema.py.
"""
from scripts.vectordb import vectordb
from schema.endpoint_schema import get_endpoint_by_name
from agents.llm_reranker import rerank_endpoint_with_llm


MIN_CONFIDENCE_SCORE = 0.45
TOP_K = 5


def select_endpoint(state: dict) -> dict:
    query = state["user_query"]
    multi = state.get("requires_multi_endpoint", False)

    if multi:
        # Parallel multi-endpoint: fetch top candidates from each bucket, rerank each.
        demand_candidates = vectordb.search(query, category="Demand Planning", limit=TOP_K)
        supply_candidates = vectordb.search(query, category="Supply Planning", limit=TOP_K)

        demand_name = _pick_one(query, demand_candidates) if demand_candidates else None
        supply_name = _pick_one(query, supply_candidates) if supply_candidates else None

        names = [n for n in (demand_name, supply_name) if n]
        selected = [_hydrate(n) for n in names if _hydrate(n)]
        if not selected:
            print("  [Selector] No endpoints found")
            return {"selected_endpoints": [], "current_endpoint_index": 0, "current_endpoint": None}
        print(f"  [Selector multi] -> {[s['endpoint_name'] for s in selected]}")
        return {"selected_endpoints": selected, "current_endpoint_index": 0, "current_endpoint": selected[0]}

    # Single-endpoint flow: search across ALL endpoints.
    candidates = vectordb.search(query, limit=TOP_K)

    if not candidates:
        print("  [Selector] No endpoints found")
        return {"selected_endpoints": [], "current_endpoint_index": 0, "current_endpoint": None}

    top_score = candidates[0]["score"]
    if top_score < MIN_CONFIDENCE_SCORE:
        print(f"  [Selector] Top score {top_score} below {MIN_CONFIDENCE_SCORE}; using top-1 anyway")

    chosen_name = _pick_one(query, candidates)

    schema = _hydrate(chosen_name)
    if not schema:
        print(f"  [Selector] '{chosen_name}' not in schema; falling back to vector top-1")
        chosen_name = candidates[0]["endpoint_name"]
        schema = _hydrate(chosen_name)
        if not schema:
            return {"selected_endpoints": [], "current_endpoint_index": 0, "current_endpoint": None}

    print(f"  [Selector] -> {chosen_name}")
    return {
        "selected_endpoints": [schema],
        "current_endpoint_index": 0,
        "current_endpoint": schema,
    }


def _pick_one(query: str, candidates: list[dict]) -> str:
    """Always call the reranker (matches standalone behavior).

    The reranker decides among all candidates using its priority rules.
    Falls back to vector top-1 only if the reranker errors or returns an
    invalid endpoint name.
    """
    if len(candidates) == 1:
        return candidates[0]["endpoint_name"]

    rerank_input = [
        {"endpoint": c["endpoint_name"], "score": c["score"]}
        for c in candidates
    ]
    try:
        result = rerank_endpoint_with_llm(query, rerank_input)
        chosen = result["selected_endpoint"]
        valid = {c["endpoint_name"] for c in candidates}
        if chosen not in valid:
            print(f"  [Selector] Rerank returned invalid '{chosen}'; using vector top-1")
            return candidates[0]["endpoint_name"]
        return chosen
    except Exception as e:
        print(f"  [Selector] Rerank error: {e}; using vector top-1")
        return candidates[0]["endpoint_name"]


def _hydrate(endpoint_name: str | None) -> dict | None:
    if not endpoint_name:
        return None
    return get_endpoint_by_name(endpoint_name)
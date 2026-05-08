"""SQL generator — uses LLM to resolve all lookup names, then assembles GraphQL variables.

Flow:
  1. LLM receives the user query + endpoint schema + DB candidates and resolves
     all entity names to their canonical DB names in one shot.
  2. Canonical names are passed to postgres.resolve_lookup for UUID resolution.
  3. Fixed variables and defaults are merged in deterministically.
  4. Anything the LLM + DB still can't resolve surfaces as unresolved_entity.
"""
import json
import os

from dotenv import load_dotenv
from groq import Groq
from sqlalchemy import text

from scripts.postgres import postgres

load_dotenv()

TABLE_LABELS = {
    "site": "site",
    "part": "part",
    "companysite": "supplier or customer",
    "process": "process",
}


def _ensure_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _get_candidates(table: str, limit: int = 50) -> list[str]:
    """Fetch candidate names from DB for LLM to choose from."""
    try:
        division = postgres._division()
        engine = postgres._get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    f"SELECT name FROM temporalfactory.{table} "
                    f"WHERE division = :division AND rowdeath IS NULL "
                    f"ORDER BY name LIMIT :limit"
                ),
                {"division": division, "limit": limit},
            ).fetchall()
        return [r[0] for r in rows if r[0]]
    except Exception as e:
        print(f"  [SQL/LLM] Could not fetch candidates from {table}: {e}")
        return []


def _llm_resolve_lookups(user_query: str, lookups: list[dict]) -> dict[str, str | None]:
    """LLM resolves all lookup names to canonical DB names in one call.

    Returns a dict of {variable_name: resolved_canonical_name_or_None}.
    """
    if not lookups:
        return {}

    # Fetch candidates for each unique table
    tables_needed = {e["table"] for e in lookups if e.get("table")}
    candidates_by_table = {t: _get_candidates(t) for t in tables_needed}

    lookup_requests = []
    for entry in lookups:
        lookup_requests.append({
            "variable": entry.get("variable"),
            "table": entry.get("table"),
            "user_provided_names": _ensure_list(entry.get("lookup_value")),
            "candidates": candidates_by_table.get(entry.get("table"), [])[:30],
        })

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("LIGHTWEIGHT_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a name resolver for a manufacturing database. "
                        "For each lookup, match the user-provided names to the closest "
                        "candidate from the database list. "
                        "Return JSON: {\"resolutions\": [{\"variable\": \"...\", \"resolved_names\": [\"...\"] or null}]}. "
                        "Use null if no candidate is close enough. "
                        "resolved_names should be a list (even for single values)."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "user_query": user_query,
                        "lookups": lookup_requests,
                    }),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=512,
        )
        result = json.loads(resp.choices[0].message.content)
        resolutions = {}
        for r in result.get("resolutions", []):
            resolutions[r["variable"]] = r.get("resolved_names")
        print(f"  [SQL/LLM] Resolved: {resolutions}")
        return resolutions
    except Exception as e:
        print(f"  [SQL/LLM] Resolution error: {e}")
        return {}


def generate_variables(state: dict) -> dict:
    endpoint = state.get("current_endpoint", {})
    fixed = endpoint.get("fixed_variables", {}) or {}
    user_vars_schema = endpoint.get("user_variables", {}) or {}
    user_query = state.get("user_query", "")

    resolved = state.get("resolved_variables") or {}
    lookups = state.get("lookups_needed") or []

    graphql_vars: dict = {}
    errors: list[str] = []
    unresolved_entities: list[dict] = []

    # 1) fixed variables
    graphql_vars.update(fixed)

    # 2) defaults
    for var_name, spec in user_vars_schema.items():
        if var_name in graphql_vars:
            continue
        default = spec.get("default_value")
        if default is not None:
            graphql_vars[var_name] = default

    # 3) resolved_variables from parameter extractor
    for var_name, value in resolved.items():
        graphql_vars[var_name] = value

    # 4) LLM resolves all lookup names to canonical DB names, then UUID lookup
    if lookups:
        llm_resolutions = _llm_resolve_lookups(user_query, lookups)

        for entry in lookups:
            if not isinstance(entry, dict):
                errors.append(f"Malformed lookup entry: {entry!r}")
                continue

            var_name = entry.get("variable")
            table = entry.get("table")
            lookup_value = entry.get("lookup_value")
            return_as = entry.get("return_as")

            if not (var_name and table and return_as):
                errors.append(f"Lookup missing required fields: {entry!r}")
                continue

            user_named_something = bool(lookup_value) and any(
                (n if isinstance(n, str) else "").strip()
                for n in _ensure_list(lookup_value)
            )

            # Use LLM-resolved names if available, else fall back to original
            llm_names = llm_resolutions.get(var_name)
            effective_lookup = llm_names if llm_names else lookup_value

            try:
                resolved_uuid = postgres.resolve_lookup(table, effective_lookup, return_as)
            except Exception as e:
                errors.append(f"Lookup failed for {var_name} ({table}): {e}")
                resolved_uuid = [] if return_as == "list" else None

            nothing_resolved = (
                (return_as == "list" and not resolved_uuid)
                or (return_as == "single" and resolved_uuid is None)
            )

            if nothing_resolved and user_named_something:
                named = _ensure_list(lookup_value)
                primary_name = next(
                    (n for n in named if isinstance(n, str) and n.strip()),
                    "the value you provided",
                )
                unresolved_entities.append({
                    "name": primary_name,
                    "table": table,
                    "variable": var_name,
                    "label": TABLE_LABELS.get(table, table),
                })
                errors.append(
                    f"User named '{primary_name}' for {var_name} ({table}) "
                    f"but it was not found in the database."
                )

            graphql_vars[var_name] = resolved_uuid

    print(f"  [SQL] graphql_vars keys: {list(graphql_vars.keys())}")
    if errors:
        print(f"  [SQL] resolution warnings: {errors}")
    if unresolved_entities:
        print(f"  [SQL] unresolved entities: {unresolved_entities}")

    # Debug: show a trimmed JSON of the graphql variables for inspection
    try:
        import json as _json
        gv = _json.dumps(graphql_vars, default=str)
        gv_trim = gv if len(gv) <= 1000 else gv[:1000] + "...[trimmed]"
    except Exception:
        gv_trim = "<unavailable>"
    print(f"  [SQL] graphql_vars (trimmed): {gv_trim}")

    return {
        "graphql_variables": graphql_vars,
        "graphql_resolution_errors": errors if errors else None,
        "unresolved_entities": unresolved_entities if unresolved_entities else None,
    }

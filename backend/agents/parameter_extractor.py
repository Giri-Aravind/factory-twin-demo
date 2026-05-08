"""
Parameter extractor — calls Groq API with the endpoint-specific system prompt
and returns the LLM's structured handoff for the SQL generator.

Inputs:  user_query (str), endpoint_name (str)
Output:  {"resolved_variables": {...}, "lookups_needed": [...], "missing_required": [...]}
         or on failure:
         {"error": "...", "raw_output": "...",
          "resolved_variables": {}, "lookups_needed": [], "missing_required": []}
"""

import json
import os
from groq import Groq
from dotenv import load_dotenv

from schema import parameter_extractor_schema
from schema.endpoint_schema import endpoint_data
from scripts.date_utils import expand_period_boundaries

load_dotenv()

MODEL_NAME = os.getenv("LIGHTWEIGHT_MODEL", "llama-3.1-8b-instant")

# Hardcoded "now" date per platform spec (Platform_Information.docx).
SIMULATION_NOW = "2025-01-01"

# Simulation data window — used as defaults when the user only specifies
# a partial date range (only `from` or only `until`).
SIMULATION_START = "2025-01-01T00:00:00Z"
SIMULATION_END = "2026-07-01T00:00:00Z"


def _get_system_prompt(endpoint_name: str) -> str:
    attr = f"{endpoint_name}_prompt"
    if not hasattr(parameter_extractor_schema, attr):
        raise ValueError(
            f"No system prompt found for endpoint '{endpoint_name}'. "
            f"Expected variable '{attr}' in parameter_extractor_schema.py."
        )
    return getattr(parameter_extractor_schema, attr)


def _drop_resolved_if_in_lookups(resolved: dict, lookups: list) -> dict:
    """
    A variable cannot be in both resolved_variables and lookups_needed.
    The lookup is authoritative; remove any duplicate from resolved_variables.
    """
    looked_up_vars = {
        entry.get("variable")
        for entry in lookups
        if isinstance(entry, dict)
    }
    for var in looked_up_vars:
        resolved.pop(var, None)
    return resolved


def _post_process_period_boundaries(resolved: dict) -> dict:
    """
    If the LLM emitted periodBoundaries as a {from, until} object,
    expand it into a list of monthly boundary timestamps.
    Partial ranges are filled with the simulation window edges.
    """
    pb = resolved.get("periodBoundaries")
    if pb is None or isinstance(pb, list):
        return resolved

    if isinstance(pb, dict):
        from_iso = pb.get("from", SIMULATION_START)
        until_iso = pb.get("until", SIMULATION_END)
        try:
            resolved["periodBoundaries"] = expand_period_boundaries(
                from_iso, until_iso
            )
        except Exception as e:
            resolved.pop("periodBoundaries", None)
            resolved["_period_boundary_error"] = str(e)

    return resolved


def _validate_missing_required(missing: list, endpoint_name: str) -> list:
    """
    Only include slots that are truly required (no default) in missing_required.
    Filters out anything the LLM over-flagged — for example, slots that have
    a schema default and therefore should not be flagged as missing.

    A slot is "truly required" when:
      - schema says required: True
      - AND default_value is None (no fallback)
    """
    schema = endpoint_data.get(endpoint_name, {})
    user_vars = schema.get("user_variables", {})
    truly_required = {
        name for name, spec in user_vars.items()
        if spec.get("required") and spec.get("default_value") is None
    }
    return [m for m in missing if m in truly_required]


def extract(user_query: str, endpoint_name: str) -> dict:
    # 1. validate the endpoint exists in the schema
    if endpoint_name not in endpoint_data:
        return {
            "error": f"Endpoint '{endpoint_name}' not found in endpoint_data.",
            "raw_output": "",
            "resolved_variables": {},
            "lookups_needed": [],
            "missing_required": [],
        }

    # 2. load the system prompt for this endpoint
    try:
        system_prompt = _get_system_prompt(endpoint_name)
    except ValueError as e:
        return {
            "error": str(e),
            "raw_output": "",
            "resolved_variables": {},
            "lookups_needed": [],
            "missing_required": [],
        }

    # 3. inject the simulation "now" date into the prompt
    try:
        system_prompt = system_prompt.format(today=SIMULATION_NOW)
    except (KeyError, IndexError) as e:
        return {
            "error": (
                f"Prompt formatting failed: {e}. Make sure all literal "
                f"curly braces in the prompt are escaped as double braces."
            ),
            "raw_output": "",
            "resolved_variables": {},
            "lookups_needed": [],
            "missing_required": [],
        }

    # 4. call Groq API with response_format="json"
    try:
        api_key = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=2048,
        )
        raw_output = response.choices[0].message.content
    except Exception as e:
        return {
            "error": f"Groq API call failed: {e}",
            "raw_output": "",
            "resolved_variables": {},
            "lookups_needed": [],
            "missing_required": [],
        }

    # 5. parse the JSON
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as e:
        return {
            "error": f"LLM returned invalid JSON: {e}",
            "raw_output": raw_output,
            "resolved_variables": {},
            "lookups_needed": [],
            "missing_required": [],
        }

    # 6. sanity-check the top-level shape; default missing keys to empty
    resolved = parsed.get("resolved_variables", {})
    lookups = parsed.get("lookups_needed", [])
    missing = parsed.get("missing_required", [])

    if not isinstance(resolved, dict):
        resolved = {}
    if not isinstance(lookups, list):
        lookups = []
    if not isinstance(missing, list):
        missing = []

    # 7. enforce: a variable lives in exactly one of resolved_variables or
    #    lookups_needed, never both
    resolved = _drop_resolved_if_in_lookups(resolved, lookups)

    # 8. post-process: expand periodBoundaries object into list, if present
    resolved = _post_process_period_boundaries(resolved)

    # 9. enforce: missing_required only contains truly-required slots
    #    (filters out anything the LLM over-flagged)
    missing = _validate_missing_required(missing, endpoint_name)

    # Debug logging: show a trimmed LLM raw output and the resolved shape
    try:
        trimmed = raw_output if len(raw_output) <= 1000 else raw_output[:1000] + "...[trimmed]"
    except Exception:
        trimmed = "<unavailable>"
    print(f"  [Params] LLM raw_output: {trimmed!r}")
    print(f"  [Params] resolved_variables keys: {list(resolved.keys())}, lookups_needed: {lookups}, missing_required: {missing}")
    return {
        "resolved_variables": resolved,
        "lookups_needed": lookups,
        "missing_required": missing,
    }


if __name__ == "__main__":
    # Quick manual smoke test
    result = extract(
        "show me the shortage analysis for Part OLIC-5678",
        "materialShortageAnalysis",
    )
    print(json.dumps(result, indent=2))
"""Entity extractor — uses LLM to extract entities from GraphQL results.

LLM is the primary extraction path for all chart types. The deterministic
per-chart-type helpers are kept as a fast fallback if the LLM call fails.
UUID resolution is always done via postgres after extraction.
"""
import json
import os

from dotenv import load_dotenv
from groq import Groq

from scripts.postgres import postgres

load_dotenv()


def _llm_extract_entities(graphql_result, carry_forward_keys: list[str]) -> dict:
    """Use LLM to extract named entities from any GraphQL result shape."""
    try:
        data_str = json.dumps(graphql_result, default=str)
        if len(data_str) > 4000:
            data_str = data_str[:4000] + "... [truncated]"

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("LIGHTWEIGHT_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract named entities from manufacturing GraphQL data. "
                        "Given raw data and a list of needed entity types, return JSON with "
                        "keys from: customers, parts, suppliers, sites, months. "
                        "Each key maps to a list of objects: {\"name\": \"...\", \"quantity\": 0, \"value\": 0}. "
                        "Only include keys that are requested AND found in the data. "
                        "Limit each list to top 10 by quantity or value. "
                        "Return {} if nothing relevant is found."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "needed_entity_types": carry_forward_keys,
                        "data": json.loads(data_str.replace("... [truncated]", "")),
                    }, default=str),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=1024,
        )
        result = json.loads(resp.choices[0].message.content)
        print(f"  [EntityExtractor/LLM] extracted keys: {list(result.keys())}")
        return result
    except Exception as e:
        print(f"  [EntityExtractor/LLM] Error: {e}")
        return {}


def extract_entities(graphql_result, chart_type: str, carry_forward_keys: list[str]) -> dict:
    """Extract entities from result data. LLM is the primary path.

    Falls back to deterministic helpers if LLM fails.
    """
    if not carry_forward_keys or graphql_result is None:
        return {}

    needs_uuids = {
        "customers": "customer_uuids" in carry_forward_keys,
        "parts": "part_uuids" in carry_forward_keys,
        "suppliers": "supplier_uuids" in carry_forward_keys,
        "sites": "site_uuids" in carry_forward_keys,
    }

    # LLM primary path
    entities = _llm_extract_entities(graphql_result, carry_forward_keys)

    # Fallback to deterministic helpers if LLM returned nothing
    if not entities:
        print(f"  [EntityExtractor] LLM returned empty, falling back to deterministic ({chart_type})")
        entities = _deterministic_extract(graphql_result, chart_type, carry_forward_keys)

    # Resolve UUIDs where requested
    _resolve_uuids(entities, needs_uuids)

    print(f"  [EntityExtractor] -> {_summary(entities)}")
    return entities


# ─── Deterministic fallback ──────────────────────────────────────────────────

def _deterministic_extract(graphql_result, chart_type: str, carry_forward_keys: list[str]) -> dict:
    needs_customers = any(k in carry_forward_keys for k in ("customer_names", "customer_uuids"))
    needs_parts = any(k in carry_forward_keys for k in ("part_names", "part_uuids"))
    needs_suppliers = any(k in carry_forward_keys for k in ("supplier_names", "supplier_uuids"))
    needs_months = "month_names" in carry_forward_keys

    if chart_type == "stacked_bar":
        return _extract_from_stacked_bar(graphql_result, needs_customers, needs_parts, needs_suppliers, needs_months)
    elif chart_type == "horizontal_bar":
        return _extract_from_horizontal_bar(graphql_result, needs_parts)
    elif chart_type == "table":
        return _extract_from_table(graphql_result, needs_customers, needs_parts, needs_suppliers)
    return {}


def _extract_from_stacked_bar(data, needs_customers, needs_parts, needs_suppliers, needs_months):
    out = {}
    if not isinstance(data, list) or not data:
        return out
    totals = {}
    months = []
    for period in data:
        start = period.get("startDate", "")
        if start:
            months.append(start[:7])
        stacks = period.get("stackDataList") or period.get("stacks", [])
        for s in stacks:
            name = s.get("name", "")
            if not name:
                continue
            qty = s.get("quantity", 0) or 0
            val = s.get("value", 0) or 0
            if name not in totals:
                totals[name] = {"name": name, "quantity": 0, "value": 0}
            totals[name]["quantity"] += qty
            totals[name]["value"] += val
    top = sorted(totals.values(), key=lambda x: x["value"] or x["quantity"], reverse=True)[:10]
    if needs_customers:
        out["customers"] = top
    if needs_parts:
        out["parts"] = top
    if needs_suppliers:
        out["suppliers"] = top
    if needs_months and months:
        out["months"] = sorted(set(months))
    return out


def _extract_from_horizontal_bar(data, needs_parts):
    out = {}
    if not isinstance(data, list):
        return out
    items = []
    for r in data:
        part_name = r.get("part", "")
        if not part_name:
            continue
        qty = sum(s.get("quantity", 0) or 0 for s in r.get("stackData", []))
        val = sum(s.get("value", 0) or 0 for s in r.get("stackData", []))
        items.append({"name": part_name, "quantity": qty, "value": val})
    items.sort(key=lambda x: x["value"], reverse=True)
    if needs_parts:
        out["parts"] = items[:10]
    return out


def _extract_from_table(data, needs_customers, needs_parts, needs_suppliers):
    out = {}
    if not isinstance(data, list) or not data:
        return out
    parts, customers, suppliers = {}, {}, {}
    for row in data:
        if not isinstance(row, dict):
            continue
        part_name = row.get("part") or row.get("purchasedPart") or row.get("purchasedPartIdentifier")
        if part_name and isinstance(part_name, str):
            if part_name not in parts:
                parts[part_name] = {"name": part_name, "quantity": 0, "value": 0}
            parts[part_name]["quantity"] += row.get("totalDemanded", 0) or 0
        supplier_name = row.get("supplier")
        if supplier_name and isinstance(supplier_name, str):
            if supplier_name not in suppliers:
                suppliers[supplier_name] = {"name": supplier_name, "quantity": 0, "value": 0}
            suppliers[supplier_name]["value"] += row.get("estimatedPrice", 0) or 0
        for item in (row.get("orders") or row.get("associatedLineItems") or []):
            if not isinstance(item, dict):
                continue
            cust = item.get("customer")
            if cust and isinstance(cust, str):
                if cust not in customers:
                    customers[cust] = {"name": cust, "quantity": 0, "value": 0}
                customers[cust]["quantity"] += item.get("quantity", 0) or 0
    if needs_parts and parts:
        out["parts"] = sorted(parts.values(), key=lambda x: x["quantity"], reverse=True)[:10]
    if needs_customers and customers:
        out["customers"] = sorted(customers.values(), key=lambda x: x["quantity"], reverse=True)[:10]
    if needs_suppliers and suppliers:
        out["suppliers"] = sorted(suppliers.values(), key=lambda x: x["value"], reverse=True)[:10]
    return out


# ─── UUID resolution ─────────────────────────────────────────────────────────

def _resolve_uuids(entities: dict, needs: dict) -> None:
    if needs.get("customers") and entities.get("customers"):
        for c in entities["customers"]:
            if "uuid" not in c:
                c["uuid"] = postgres.resolve_lookup("companysite", c["name"], "single")
    if needs.get("parts") and entities.get("parts"):
        for p in entities["parts"]:
            if "uuid" not in p:
                p["uuid"] = postgres.resolve_lookup("part", p["name"], "single")
    if needs.get("suppliers") and entities.get("suppliers"):
        for s in entities["suppliers"]:
            if "uuid" not in s:
                s["uuid"] = postgres.resolve_lookup("companysite", s["name"], "single")
    if needs.get("sites") and entities.get("sites"):
        for s in entities["sites"]:
            if "uuid" not in s:
                s["uuid"] = postgres.resolve_lookup("site", s["name"], "single")


def _summary(entities: dict) -> str:
    parts = []
    for k, v in entities.items():
        parts.append(f"{k}={len(v)}" if isinstance(v, list) else f"{k}={v}")
    return ", ".join(parts) if parts else "no entities"

# llm_reranker.py

import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = os.getenv("LIGHTWEIGHT_MODEL", "llama-3.1-8b-instant")


ENDPOINT_SHORT_DESCRIPTIONS = {
    "demandByFulfillmentDonut": """
One total aggregate demand snapshot.
Use only when the user asks for total/overall/aggregate demand directly.
Does not identify customers, parts, NPI parts, suppliers, materials, or categories.
""",

    "demandByFulfillmentHistogram": """
Monthly aggregate demand trend.
Use for monthly demand, demand by month, peak month, highest demand month,
lowest demand month, or comparing demand dollars/quantity across months.
""",

    "monthlyDemandByCategory": """
Monthly demand split by a category.
Use when the user asks demand by customer, platform, order type, part,
product group, category, split by, grouped by, or broken down by.
""",

    "categoryDemandPareto": """
Part-level demand drill-down for a selected time period.
Use for top parts, parts driving demand, underlying parts, demand Pareto,
or drilling into a month/period/bar.
""",

    "NewPartIntroductionDemandTable": """
NPI demand table.
Use for NPI, new parts, new part introduction, first article, FAI,
parts not made recently, parts with no recent production, or questions where
the answer depends on identifying NPI parts first.
""",

    "buyerActions": """
Buyer actions and purchase order placement alerts.
Use for procurement actions, PO placement, long lead time parts,
what buyers should order, quantity to purchase, or buyer worklist.
""",

    "suppliedMaterialDemandBySupplier": """
Bought/supplied material demand by supplier.
Use for material demand by supplier, vendor demand, supplier demand profile,
or purchased part demand grouped by supplier.
""",

    "suppliedMaterialDemandByMaterial": """
Bought/supplied material demand for a selected material, purchased part,
or component. Use for demand profile of this material/part/component.
""",

    "materialShortageAnalysis": """
Material shortage, inventory coverage, supply gap, stockout risk,
demand versus inventory, or demand versus purchase orders for a selected material.
""",

    "ospPartDemand": """
Outside processing / OSP demand.
Use for OSP, outside processing, outsourced processing, outside vendor,
external processing, OSP supplier, or OSP process demand.
""",
}


def extract_json_from_text(text: str) -> dict:
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No valid JSON object found in LLM response: {text}")

    return json.loads(text[start : end + 1])


def rerank_endpoint_with_llm(user_query: str, candidates: list[dict]) -> dict:
    """
    Rerank endpoint candidates using Groq API.

    Input candidates:
    [
        {
            "endpoint": "demandByFulfillmentDonut",
            "score": 0.76,
            "selection_text": "..."
        }
    ]

    Output:
    {
        "selected_endpoint": "...",
        "confidence": 0.0,
        "reason": "..."
    }
    """

    candidate_text = ""

    for idx, candidate in enumerate(candidates, start=1):
        endpoint = candidate["endpoint"]
        score = candidate["score"]

        short_description = ENDPOINT_SHORT_DESCRIPTIONS.get(
            endpoint,
            "No short description available.",
        )

        candidate_text += f"""
Candidate {idx}
Endpoint name: {endpoint}
Vector score: {score}
Endpoint meaning:
{short_description}
---
"""

    prompt = f"""
You are an endpoint selection reranker for a manufacturing planning analytics system.

You must choose the SINGLE best endpoint for the user's question.

User question:
{user_query}

Candidate endpoints:
{candidate_text}

CRITICAL ROUTING PRINCIPLE:
Choose the endpoint needed to answer the MAIN dependency in the question,
not the endpoint matching a single surface phrase.

Examples:
- "What is the overall demand for the customer with most NPI parts?"
  Correct endpoint: NewPartIntroductionDemandTable
  Reason: The system must first identify the customer with the most NPI parts. A total demand endpoint cannot identify NPI parts or customers.

- "Show total demand for Minneapolis"
  Correct endpoint: demandByFulfillmentDonut
  Reason: Direct total demand snapshot.

- "Identify the month with most demand in dollars"
  Correct endpoint: demandByFulfillmentHistogram
  Reason: Need monthly demand values to compare months.

- "Show demand by customer"
  Correct endpoint: monthlyDemandByCategory
  Reason: Need customer category breakdown.

- "Show top parts for January"
  Correct endpoint: categoryDemandPareto
  Reason: Need part-level drill-down for a period.

- "Is this material short?"
  Correct endpoint: materialShortageAnalysis
  Reason: Need shortage, inventory, and purchase order coverage.

- "What purchase orders need to be placed?"
  Correct endpoint: buyerActions
  Reason: Need buyer action / PO placement alerts.

- "Show material demand by supplier"
  Correct endpoint: suppliedMaterialDemandBySupplier
  Reason: Need bought material demand grouped by supplier.

- "Show demand for this material"
  Correct endpoint: suppliedMaterialDemandByMaterial
  Reason: Need demand profile for a selected material.

- "Show OSP demand by process"
  Correct endpoint: ospPartDemand
  Reason: OSP/outside processing dominates.

Decision rules:
1. If the question contains NPI, new parts, first article, FAI, parts not made recently,
   or asks for something based on NPI parts, choose NewPartIntroductionDemandTable.
2. If the question asks for a customer/supplier/material/month/part "with most X",
   choose the endpoint that can identify that X first.
3. Do not choose demandByFulfillmentDonut just because the phrase "overall demand" appears.
   Only choose it when the user directly asks for one total demand snapshot and no other
   special condition must be identified first.
4. If the question needs monthly comparison, peak month, highest month, or demand by month,
   choose demandByFulfillmentHistogram.
5. If the question needs category breakdown by customer/platform/order type/category,
   choose monthlyDemandByCategory.
6. If the question needs top parts or drill-down into a period, choose categoryDemandPareto.
7. If the question needs shortage/inventory/PO coverage, choose materialShortageAnalysis.
8. If the question needs procurement/buyer/PO placement action, choose buyerActions.
9. If the question needs supplier-level bought material demand, choose suppliedMaterialDemandBySupplier.
10. If the question needs selected material/part/component demand profile, choose suppliedMaterialDemandByMaterial.
11. If the question needs OSP/outside processing demand, choose ospPartDemand.

Return ONLY valid JSON.
Do not include markdown.
Do not include text outside JSON.

JSON format:
{{
  "selected_endpoint": "endpointName",
  "confidence": 0.0,
  "reason": "short reason"
}}
"""

    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict endpoint router. "
                    "Always choose the endpoint required by the main dependency of the question. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
        top_p=0.1,
        max_tokens=256,
    )

    content = response.choices[0].message.content

    parsed = extract_json_from_text(content)

    if "selected_endpoint" not in parsed:
        raise ValueError(f"LLM response missing selected_endpoint: {parsed}")

    return parsed
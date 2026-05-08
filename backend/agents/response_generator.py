"""Response generator — Python computes facts, LLM writes sentence."""
import json
import os
from groq import Groq
from dotenv import load_dotenv
from schema.response_schema import response_system_prompt

load_dotenv()


def generate_response(state: dict) -> dict:
    results = state.get("endpoint_results", [])
    if not results:
        return {"final_response": "I couldn't retrieve any data.", "chart_config": None}

    r = results[0]
    data = r.get("data")
    chart_type = r.get("chart_type", "table")
    display_name = r.get("display_name", "")
    ep_name = r.get("endpoint_name", "")

    if data is None or (isinstance(data, list) and len(data) == 0):
        return {"final_response": "No data found for your query.", "chart_config": None}

    summary = _compute_summary(data, chart_type)
    print(f"  [Response] Summary:\n{summary}")

    payload = json.dumps({
        "user_question": state["user_query"],
        "chart_type": chart_type,
        "data_summary": summary,
    }, indent=2)

    try:
        api_key = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.getenv("LIGHTWEIGHT_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {"role": "system", "content": response_system_prompt},
                {"role": "user", "content": payload},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            top_p=0.1,
            max_tokens=1024,
        )
        result = json.loads(resp.choices[0].message.content)
        nl = result.get("response", summary)
    except Exception:
        nl = summary

    chart = _build_chart(data, chart_type, display_name, ep_name)
    print(f"  [Response] OK ({chart_type})")
    return {"final_response": nl, "chart_config": chart}


# ─── Summary computation ────────────────────────────────────────────────────

def _compute_summary(data, chart_type):
    if chart_type == "donut":
        segs = data.get("stackDataList", []) if isinstance(data, dict) else data if isinstance(data, list) else []
        if not segs: return "No demand data."
        tq = sum(s.get("quantity", 0) for s in segs)
        tv = sum(s.get("value", 0) for s in segs)
        lines = [f"Total orders: {tq:,}", f"Total value: ${tv:,.2f}"]
        for s in segs:
            pct = (s["quantity"] / tq * 100) if tq > 0 else 0
            lines.append(f"  - {s['name']}: {s['quantity']:,} orders (${s['value']:,.2f}, {pct:.1f}%)")
        return "\n".join(lines)

    elif chart_type == "stacked_bar":
        if not isinstance(data, list) or not data: return "No monthly data."
        months = []
        has_values = False
        for p in data:
            stacks = p.get("stackDataList") or p.get("stacks", [])
            mq = sum(s.get("quantity", 0) for s in stacks)
            mv = sum(s.get("value", 0) for s in stacks)
            if mv > 0:
                has_values = True
            months.append({
                "month": p.get("startDate", "")[:7],
                "quantity": mq,
                "value": mv,
            })
        bq = sorted(months, key=lambda x: x["quantity"], reverse=True)
        tq = sum(m["quantity"] for m in months)
        series = set()
        for p in data:
            for s in (p.get("stackDataList") or p.get("stacks", [])):
                series.add(s.get("name", ""))
        lines = [
            f"Months: {len(months)}",
            f"Highest quantity: {bq[0]['month']} ({bq[0]['quantity']:,})",
            f"Lowest quantity: {bq[-1]['month']} ({bq[-1]['quantity']:,})",
            f"Total: {tq:,} units",
            f"Avg/month: {tq // len(months):,}" if months else "",
        ]
        if has_values:
            bv = sorted(months, key=lambda x: x["value"], reverse=True)
            tv = sum(m["value"] for m in months)
            lines.insert(2, f"Highest value: {bv[0]['month']} (${bv[0]['value']:,.2f})")
            lines[3] = f"Total: {tq:,} units, ${tv:,.2f}"
        if series:
            lines.append(f"Categories: {', '.join(sorted(series))}")
        return "\n".join(lines)

    elif chart_type == "horizontal_bar":
        if not isinstance(data, list): return "No part data."
        items = [
            {
                "part": r.get("part", ""),
                "qty": sum(s.get("quantity", 0) for s in r.get("stackData", [])),
                "val": sum(s.get("value", 0) for s in r.get("stackData", [])),
            }
            for r in data
        ]
        items.sort(key=lambda x: x["val"], reverse=True)
        tv = sum(i["val"] for i in items)
        lines = [f"Parts: {len(items)}", f"Total value: ${tv:,.2f}", "Top 5:"]
        for i, it in enumerate(items[:5]):
            lines.append(f"  {i+1}. {it['part']}: {it['qty']:,} units, ${it['val']:,.2f}")
        return "\n".join(lines)

    elif chart_type == "combo_bar_line":
        if not isinstance(data, dict): return "No shortage data."
        d = data.get("demandQuantity", [])
        po = data.get("purchaseOrderQuantity", [])
        inv = data.get("inventoryValue", [])
        lines = [
            f"Inventory: {data.get('quantityFromInventory', 0):,}",
            f"Overdue POs: {data.get('overduePurchaseOrderQuantity', 0):,}",
        ]
        if d: lines.append(f"Avg demand: {sum(d) / len(d):,.1f}/month")
        if po: lines.append(f"Avg PO: {sum(po) / len(po):,.1f}/month")
        if inv:
            neg = [i + 1 for i, v in enumerate(inv) if v < 0]
            lines.append(f"Goes negative in month index(es): {neg}" if neg else "Stays positive")
        return "\n".join(lines)

    elif chart_type == "table":
        if isinstance(data, list): return f"Table: {len(data)} rows"
        return "Table data"

    return f"Data: {type(data).__name__}"


# ─── Chart builders ──────────────────────────────────────────────────────────

def _build_chart(data, chart_type, display_name, ep_name):
    base = {"chart_type": chart_type, "title": display_name, "endpoint": ep_name}

    if chart_type == "donut":
        segs = data.get("stackDataList", []) if isinstance(data, dict) else data if isinstance(data, list) else []
        return {
            **base,
            "segments": [
                {"name": s["name"], "quantity": s.get("quantity", 0), "value": s.get("value", 0)}
                for s in segs
            ],
            "total_quantity": sum(s.get("quantity", 0) for s in segs),
            "total_value": sum(s.get("value", 0) for s in segs),
        }

    elif chart_type == "stacked_bar":
        if not isinstance(data, list): return {**base, "bars": []}
        bars, series = [], set()
        for p in data:
            stacks = p.get("stackDataList") or p.get("stacks", [])
            bar = {"label": _fmt(p.get("startDate", "")), "stacks": {}}
            for s in stacks:
                n = s.get("name", "")
                series.add(n)
                bar["stacks"][n] = {"quantity": s.get("quantity", 0), "value": s.get("value", 0)}
            bars.append(bar)
        return {**base, "bars": bars, "series": sorted(series)}

    elif chart_type == "horizontal_bar":
        if not isinstance(data, list): return {**base, "items": []}
        items = [
            {
                "part": r.get("part", ""),
                "quantity": sum(s.get("quantity", 0) for s in r.get("stackData", [])),
                "value": sum(s.get("value", 0) for s in r.get("stackData", [])),
            }
            for r in data
        ]
        items.sort(key=lambda x: x["value"], reverse=True)
        return {**base, "items": items}

    elif chart_type == "combo_bar_line":
        if not isinstance(data, dict): return base
        return {
            **base,
            "demand_quantities": data.get("demandQuantity", []),
            "purchase_order_quantities": data.get("purchaseOrderQuantity", []),
            "overdue_po_quantity": data.get("overduePurchaseOrderQuantity", 0),
            "current_inventory": data.get("quantityFromInventory", 0),
            "inventory_values": data.get("inventoryValue", []),
        }

    elif chart_type == "table":
        if not isinstance(data, list): return {**base, "rows": []}
        if data and isinstance(data[0], dict):
            return {**base, "rows": data, "columns": list(data[0].keys())}
        return {**base, "rows": data}

    return {**base, "data": data}


def _fmt(d):
    if not d: return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(d.split("[")[0].replace("Z", "+00:00"))
        return dt.strftime("%b %Y")
    except Exception:
        return d[:10]
"""Intent detector — classifies user query, detects continue_plan and is_multi_step."""
import json
import os
from groq import Groq
from dotenv import load_dotenv
from schema.intent_schema import intent_system_prompt

load_dotenv()


VALID_INTENTS = {
    "general_chat",
    "new_data_query",
    "follow_up",
    "clarification_response",
    "continue_plan",
    "out_of_scope",
}


def parse_json_safely(raw_text: str) -> dict:
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")

        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw_text[start:end + 1])
            except json.JSONDecodeError:
                pass

    return {
        "intent": "out_of_scope",
        "requires_multi_endpoint": False,
        "is_multi_step": False,
        "confidence": 0.0,
        "reason": "Model did not return valid JSON.",
        "raw_response": raw_text,
    }


def normalize_result(result: dict) -> dict:
    intent = result.get("intent")

    if intent not in VALID_INTENTS:
        result["intent"] = "out_of_scope"

    if not isinstance(result.get("requires_multi_endpoint"), bool):
        result["requires_multi_endpoint"] = False

    if not isinstance(result.get("is_multi_step"), bool):
        result["is_multi_step"] = False

    confidence = result.get("confidence")
    if not isinstance(confidence, (int, float)):
        result["confidence"] = 0.0

    if not result.get("reason"):
        result["reason"] = "No reason provided."

    # is_multi_step is only valid for new_data_query
    if result["intent"] != "new_data_query":
        result["is_multi_step"] = False

    # Multi-endpoint and multi-step are mutually exclusive
    if result["is_multi_step"]:
        result["requires_multi_endpoint"] = False

    # general_chat / out_of_scope / continue_plan have no multi-* flags
    if result["intent"] in {"general_chat", "out_of_scope", "continue_plan", "clarification_response"}:
        result["requires_multi_endpoint"] = False
        result["is_multi_step"] = False

    result["source"] = "llm_only"

    return result


def build_active_plan_summary(plan: dict | None) -> dict | None:
    """Build a compact summary of the active plan for the intent classifier."""
    if not plan or not plan.get("steps"):
        return None

    steps = plan["steps"]
    completed = [s["description"] for s in steps if s.get("status") == "complete"]

    # Find next pending step whose dependencies are all complete
    next_pending = None
    for s in steps:
        if s.get("status") != "pending":
            continue
        deps = s.get("depends_on", [])
        deps_ok = all(
            any(p.get("step_number") == d and p.get("status") == "complete" for p in steps)
            for d in deps
        )
        if deps_ok or not deps:
            next_pending = s["description"]
            break

    if not next_pending:
        # No pending step left — plan is done; do not surface as active
        return None

    return {
        "completed_steps": completed,
        "next_pending_step": next_pending,
        "total_steps": len(steps),
    }


def build_user_payload(state: dict) -> str:
    user_query = state.get("user_query", "").strip()
    history = state.get("conversation_history", [])

    last_user_query = None
    for msg in reversed(history):
        if msg.get("role") == "user":
            last_user_query = msg.get("content", "")
            break

    recent_user_queries = [
        msg.get("content", "")
        for msg in history[-8:]
        if msg.get("role") == "user"
    ]

    active_plan = build_active_plan_summary(state.get("query_plan"))

    user_payload = json.dumps(
        {
            "pending_clarification": state.get("pending_clarification"),
            "last_endpoint_used": state.get("last_endpoint_used", "none"),
            "active_plan": active_plan,
            "last_user_query": last_user_query,
            "recent_user_queries": recent_user_queries,
            "current_user_query": user_query,
        },
        indent=2,
    )

    return user_payload


def detect_intent_llm_only(state: dict) -> dict:
    user_payload = build_user_payload(state)
    model = os.getenv("LIGHTWEIGHT_MODEL", "llama-3.1-8b-instant")
    api_key = os.getenv("GROQ_API_KEY")
    
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": intent_system_prompt},
            {"role": "user", "content": user_payload},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        top_p=0.1,
        max_tokens=1024,
    )

    raw_output = response.choices[0].message.content
    result = parse_json_safely(raw_output)
    result = normalize_result(result)

    print(
        f"  [Intent] -> {result['intent']} "
        f"(multi_endpoint={result['requires_multi_endpoint']}, "
        f"multi_step={result['is_multi_step']})"
    )

    return result


# Alias for supervisor import
detect_intent = detect_intent_llm_only


def main():
    """Interactive playground for testing the intent detector."""
    conversation_history = []
    pending_clarification = None
    last_endpoint_used = "none"
    query_plan = None

    print("\nIntent Detector Playground")
    print("Commands: /exit, /clear, /history, /pending, /plan\n")

    while True:
        user_query = input("You: ").strip()
        if not user_query:
            continue

        if user_query.lower() == "/exit":
            break
        if user_query.lower() == "/clear":
            conversation_history = []
            pending_clarification = None
            last_endpoint_used = "none"
            query_plan = None
            print("History cleared.\n")
            continue
        if user_query.lower() == "/history":
            for msg in conversation_history:
                if msg.get("role") == "user":
                    print(f"- {msg.get('content')}")
            continue
        if user_query.lower() == "/pending":
            pending_clarification = "testing_pending" if pending_clarification is None else None
            print(f"pending = {pending_clarification}\n")
            continue
        if user_query.lower() == "/plan":
            if query_plan is None:
                query_plan = {
                    "steps": [
                        {"step_number": 1, "description": "Top 10 customers", "status": "complete"},
                        {"step_number": 2, "description": "Worst OTD among them", "status": "pending", "depends_on": [1]},
                    ]
                }
            else:
                query_plan = None
            print(f"plan = {query_plan}\n")
            continue

        state = {
            "user_query": user_query,
            "conversation_history": conversation_history,
            "pending_clarification": pending_clarification,
            "last_endpoint_used": last_endpoint_used,
            "query_plan": query_plan,
        }

        result = detect_intent_llm_only(state)
        print(f"\n{json.dumps(result, indent=2)}\n")

        conversation_history.append({"role": "user", "content": user_query})

        if result.get("intent") == "new_data_query":
            last_endpoint_used = "mock_endpoint"
        if result.get("intent") == "clarification_response":
            pending_clarification = None


if __name__ == "__main__":
    main()

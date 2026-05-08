"""Entry point — load history + plan, call graph, save messages."""
import os
from dotenv import load_dotenv

from agents.supervisor import compiled_graph
from scripts.chatdb import chatdb
from agents import pipeline_tracker as tracker

load_dotenv()


class Main:

    def process_query(self, user_query, conversation_id=None):
        print(f"\n{'='*60}\nProcessing: {user_query}\n{'='*60}")

        if not conversation_id:
            try:
                conversation_id = chatdb.create_conversation()
            except Exception:
                conversation_id = "local"

        try:
            history = chatdb.get_messages(
                conversation_id,
                limit=int(os.getenv("CONTEXT_WINDOW_MESSAGES", "10")),
            )
        except Exception:
            history = []

        # Load session context: walk back through assistant messages,
        # skipping ones with no real content (general_chat, out_of_scope)
        last_ep = None
        pending = None
        last_plan = None
        for m in reversed(history):
            if m.get("role") != "assistant":
                continue
            meta = m.get("metadata") or {}
            if not isinstance(meta, dict):
                continue

            # Plan: most recent non-null plan with pending steps wins
            if last_plan is None:
                p = meta.get("query_plan")
                if p and any(s.get("status") == "pending" for s in p.get("steps", [])):
                    last_plan = p

            # Endpoint: most recent assistant turn that actually used an endpoint
            if last_ep is None:
                eps = meta.get("endpoints") or []
                if eps:
                    last_ep = eps[0]

            if pending is None:
                pending = meta.get("pending_clarification")

            # Stop when we have everything we need
            if last_ep is not None and last_plan is not None:
                break

        state = {
            "user_query": user_query,
            "conversation_history": history,
            "conversation_id": conversation_id,
            "intent": "",
            "requires_multi_endpoint": False,
            "is_multi_step": False,
            "last_endpoint_used": last_ep,
            "pending_clarification": pending,
            "needs_clarification": False,
            "clarification_question": "",
            "selected_endpoints": [],
            "current_endpoint_index": 0,
            "current_endpoint": None,
            "resolved_variables": None,
            "lookups_needed": None,
            "missing_required": None,
            "graphql_variables": None,
            "graphql_result": None,
            "graphql_error": None,
            "graphql_resolution_errors": None,
            "unresolved_entities": None,
            "endpoint_results": [],
            "final_response": None,
            "chart_config": None,
            "query_plan": last_plan,
            "carry_forward_entities": None,
            "step_history": {},
            "errors": [],
        }

        # If the assistant previously asked a clarification question and
        # set `pending_clarification` in the last assistant metadata, treat
        # the incoming user message deterministically as a clarification
        # response. This avoids misclassification by the intent LLM and
        # ensures the reply resumes the prior flow.
        if state.get("pending_clarification"):
            state["intent"] = "clarification_response"

        try:
            tracker.start_run()
            final = compiled_graph.invoke(state)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "response": str(e),
                "chart_config": None,
                "needs_clarification": False,
                "conversation_id": conversation_id,
            }

        response = final.get("final_response") or final.get("clarification_question") or ""

        # Save messages
        try:
            chatdb.add_message(conversation_id, "user", user_query)
            endpoints = final.get("selected_endpoints", [])
            chatdb.add_message(
                conversation_id,
                "assistant",
                response,
                metadata={
                    "intent": final.get("intent"),
                    "endpoints": [e.get("endpoint_name") for e in endpoints],
                    "chart_config": final.get("chart_config"),
                    "pending_clarification": (
                        final.get("pending_clarification")
                        if final.get("needs_clarification")
                        else None
                    ),
                    "query_plan": final.get("query_plan"),
                    "is_multi_step": final.get("is_multi_step", False),
                },
            )
        except Exception as e:
            print(f"  Save error: {e}")

        plan_status = ""
        if final.get("query_plan"):
            plan = final["query_plan"]
            done = sum(1 for s in plan.get("steps", []) if s.get("status") == "complete")
            total = len(plan.get("steps", []))
            plan_status = f", plan={done}/{total}"

        print(f"\n{'='*60}\nDone (intent: {final.get('intent')}{plan_status})\n{'='*60}")

        return {
            "success": True,
            "response": response,
            "chart_config": final.get("chart_config"),
            "needs_clarification": final.get("needs_clarification", False),
            "clarification_question": final.get("clarification_question", ""),
            "metadata": {
                "intent": final.get("intent"),
                "endpoints": [e.get("endpoint_name") for e in final.get("selected_endpoints", [])],
                "is_multi_step": final.get("is_multi_step", False),
                "query_plan": final.get("query_plan"),
            },
            "pipeline_steps": tracker.get_steps(),
            "conversation_id": conversation_id,
        }


main = Main()
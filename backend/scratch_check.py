"""Pipeline with a missing required slot (selectedMaterial)."""
from agents.supervisor import compiled_graph

final = compiled_graph.invoke({
    "user_query": "Is this material short?",
    "conversation_history": [],
    "conversation_id": "test-missing-1",
    "endpoint_results": [],
    "errors": [],
    "step_history": {},
})

print("\n" + "=" * 60)
print("MISSING-REQUIRED PATH")
print("=" * 60)
print(f"intent:               {final.get('intent')}")
print(f"endpoint:             {(final.get('selected_endpoints') or [{}])[0].get('endpoint_name')}")
print(f"missing_required:     {final.get('missing_required')}")
print(f"needs_clarification:  {final.get('needs_clarification')}")
print(f"clarification_question:")
print(f"  {final.get('clarification_question')}")
print(f"graphql_result:       {final.get('graphql_result')}")
print(f"graphql_error:        {final.get('graphql_error')}")
print(f"final_response:")
print(f"  {(final.get('final_response') or '(none)')[:300]}")
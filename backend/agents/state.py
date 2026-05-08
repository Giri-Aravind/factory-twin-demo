"""Shared workflow state for LangGraph."""
from typing import TypedDict, Any


class WorkflowState(TypedDict, total=False):
    user_query: str
    conversation_history: list[dict[str, str]]
    conversation_id: str

    intent: str
    requires_multi_endpoint: bool
    is_multi_step: bool

    last_endpoint_used: str | None
    pending_clarification: dict[str, Any] | None

    needs_clarification: bool
    clarification_question: str

    selected_endpoints: list[dict[str, Any]]
    current_endpoint_index: int
    current_endpoint: dict[str, Any] | None

    # Parameter extractor output (new contract)
    resolved_variables: dict[str, Any] | None
    lookups_needed: list[dict[str, Any]] | None
    missing_required: list[str] | None

    graphql_variables: dict[str, Any] | None
    graphql_result: Any | None
    graphql_error: str | None
    graphql_resolution_errors: list[str] | None
    unresolved_entities: list[dict[str, Any]] | None

    endpoint_results: list[dict[str, Any]]

    final_response: str | None
    chart_config: dict[str, Any] | None

    # Multi-step query support
    query_plan: dict[str, Any] | None
    carry_forward_entities: dict[str, Any] | None

    step_history: dict[str, dict[str, Any]]
    errors: list[str]

    # Internal signal from clarification_response_node to params_node:
    # when True, params_node skips extraction and uses pre-populated lookups
    _clarification_resume: bool
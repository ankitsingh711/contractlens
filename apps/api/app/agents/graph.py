import uuid

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.nodes import (
    abstain,
    build_retrieve_node,
    classify_query,
    evaluate_evidence,
    final_response,
    plan,
    reason,
    route_on_evidence,
    validate_citations_node,
    validate_claims,
)
from app.agents.state import AgentState

# Node names, in the order they can execute — also used by the agent
# service to assign each recorded AgentStep a stable, human-readable name
# for the trace UI (see docs/agent.md for the full diagram).
NODE_NAMES = [
    "classify_query",
    "plan",
    "retrieve",
    "evaluate_evidence",
    "reason",
    "abstain",
    "validate_claims",
    "validate_citations",
    "final_response",
]


def build_agent_graph(db: AsyncSession, organization_id: uuid.UUID):
    graph = StateGraph(AgentState)

    graph.add_node("classify_query", classify_query)
    graph.add_node("plan", plan)
    graph.add_node("retrieve", build_retrieve_node(db, organization_id))
    graph.add_node("evaluate_evidence", evaluate_evidence)
    graph.add_node("reason", reason)
    graph.add_node("abstain", abstain)
    graph.add_node("validate_claims", validate_claims)
    graph.add_node("validate_citations", validate_citations_node)
    graph.add_node("final_response", final_response)

    graph.add_edge(START, "classify_query")
    graph.add_edge("classify_query", "plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "evaluate_evidence")
    graph.add_conditional_edges(
        "evaluate_evidence", route_on_evidence, {"reason": "reason", "abstain": "abstain"}
    )
    graph.add_edge("reason", "validate_claims")
    graph.add_edge("validate_claims", "validate_citations")
    graph.add_edge("abstain", "validate_citations")
    graph.add_edge("validate_citations", "final_response")
    graph.add_edge("final_response", END)

    return graph.compile()

from langgraph.graph import StateGraph, END
from .utils.state import AgentState
from .utils.nodes import (
    research_node,
    verifier_node,
    synthesizer_node,
    critic_node,
    editor_node
)

workflow = StateGraph(AgentState)

workflow.add_node("researcher", research_node)
workflow.add_node("verifier", verifier_node)
workflow.add_node("synthesizer", synthesizer_node)
workflow.add_node("critic", critic_node)
workflow.add_node("editor", editor_node)


workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "verifier")
workflow.add_edge("verifier", "synthesizer")
workflow.add_edge("synthesizer", "critic")


def check_quality(state: AgentState):
    
    if state.get("revision_count", 0) > 3:
        return "editor" 
    
    if state.get("critique_score", 0) >= 7:
        return "editor"
    else:
        return "synthesizer"

workflow.add_conditional_edges(
    "critic",
    check_quality,
    {
        "editor": "editor",
        "synthesizer": "synthesizer" 
    }
)

workflow.add_edge("editor", END)

graph = workflow.compile()

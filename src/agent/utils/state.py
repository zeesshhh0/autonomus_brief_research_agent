from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    topic: str
    research_constraints: dict
    
    raw_claims: List[dict] 
    sources: List[str]
    
    verified_claims: List[dict]
    rejected_claims: List[dict]
    
    draft_brief: dict  
    
    critique_score: int
    critique_feedback: str
    revision_count: int 
    
    final_doc: str
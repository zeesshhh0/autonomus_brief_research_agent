from typing import List
import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import create_agent
from .state import AgentState
from .prompts import (
    RESEARCH_SYSTEM_PROMPT,
    VERIFIER_SYSTEM_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT,
    CRITIC_SYSTEM_PROMPT,
    EDITOR_SYSTEM_PROMPT,
)
from .schemas import (
    ResearchOutput,
    VerifierOutput,
    ResearchBrief,
    CritiqueResult,
    EditorOutput,
)
from .llm import get_llm

from .tools import read_webpage, search_tool, search_wikipedia

fast_llm = get_llm(mode="fast")
smart_llm = get_llm(mode="smart")

def research_node(state: AgentState):
    """
    Research Agent: Gathers raw data points based on topic and constraints.
    """
    topic = state["topic"]
    constraints = state["research_constraints"]
    
    human_prompt = f"Topic: {topic}\nConstraints: {constraints}"
    
    agent = create_agent(
        model=fast_llm,
        tools=[search_tool, search_wikipedia],
        response_format=ResearchOutput,
        debug=True,
    )
    
    response = agent.invoke({'messages': [
        SystemMessage(content=RESEARCH_SYSTEM_PROMPT), 
        HumanMessage(content=human_prompt)
    ]})
    
    findings = [f.model_dump() for f in response['structured_response'].findings]
    
    sources = list(set([f['source_url'] for f in findings]))
    
    return {
        "raw_claims": findings,
        "sources": sources
    }

def verifier_node(state: AgentState):
    """
    Source Verifier: Filters claims based on heuristics and checks.
    """
    raw_claims = state["raw_claims"]
    
    serialized_claims = json.dumps(raw_claims, indent=2)
    
    system_prompt = VERIFIER_SYSTEM_PROMPT
    
    agent = create_agent(
        model=fast_llm,
        tools=[search_tool, search_wikipedia, read_webpage],
        response_format=VerifierOutput,
        debug=True,
    )

    response = agent.invoke({'messages': [
        SystemMessage(content=system_prompt),
        HumanMessage(content=serialized_claims)
    ]})
    
    # Map back to claims to separate verified vs rejected
    verified_claims = []
    rejected_claims = []
    
    # Let's assume claim_id corresponds to the index in raw_claims.
    reviews = response['structured_response'].reviews
    
    for review in reviews:
        idx = review.claim_id
        if 0 <= idx < len(raw_claims):
            claim = raw_claims[idx].copy()
            # Add verification metadata
            claim['reliability_score'] = review.reliability_score
            
            if review.is_verified:
                verified_claims.append(claim)
            else:
                claim['rejection_reason'] = review.rejection_reason
                rejected_claims.append(claim)
                
    return {
        "verified_claims": verified_claims,
        "rejected_claims": rejected_claims
    }

def synthesizer_node(state: AgentState):
    """
    Synthesizer: Builds the brief from verified claims.
    """
    verified_claims = state["verified_claims"]
    
    # Assign temporary IDs for the synthesizer to reference
    claims_with_ids = []
    for i, claim in enumerate(verified_claims):
        c = claim.copy()
        c['claim_id'] = i  # Local ID for this brief
        claims_with_ids.append(c)
        
    serialized_claims = json.dumps(claims_with_ids, indent=2)
    
    system_prompt = SYNTHESIZER_SYSTEM_PROMPT
    
    agent = create_agent(
        model=fast_llm,
        tools=[],
        response_format=ResearchBrief,
        debug=True,
    )

    response = agent.invoke({'messages': [
        SystemMessage(content=system_prompt),
        HumanMessage(content=serialized_claims)
    ]})
    
    return {
        "draft_brief": response['structured_response'].model_dump()
    }

def critic_node(state: AgentState):
    """
    Critic: Quality assurance.
    """
    draft_brief = state["draft_brief"]
    original_query = state["topic"] # Using topic as query
    
    serialized_brief = json.dumps(draft_brief, indent=2)
    
    system_prompt = CRITIC_SYSTEM_PROMPT.format(original_query=original_query)
    
    agent = create_agent(
        model=smart_llm,
        tools=[],
        response_format=CritiqueResult,
        debug=True,
    )

    response = agent.invoke({'messages': [
        SystemMessage(content=system_prompt),
        HumanMessage(content=serialized_brief)
    ]})
    
    critique = response['structured_response']

    return {
        "critique_score": critique.quality_score,
        "critique_feedback": critique.feedback,
        "revision_count": state.get("revision_count", 0) + 1
    }

def editor_node(state: AgentState):
    """
    Editor: Formatting and tone.
    """
    draft_brief = state["draft_brief"]
    audience = state.get("research_constraints", {}).get("audience", "General")
    
    serialized_brief = json.dumps(draft_brief, indent=2)
    
    system_prompt = EDITOR_SYSTEM_PROMPT.format(audience=audience)
    agent = create_agent(
        model=smart_llm,
        tools=[],
        response_format=EditorOutput,
        debug=True,
    )

    response = agent.invoke({'messages': [
        SystemMessage(content=system_prompt),
        HumanMessage(content=serialized_brief)
    ]})
    
    return {
        "final_doc": response['structured_response'].final_doc
    }

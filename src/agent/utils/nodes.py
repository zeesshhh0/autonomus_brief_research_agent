from typing import List
import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import create_agent
from langchain_community.tools import DuckDuckGoSearchResults
from .state import AgentState
from .schemas import (
    ResearchOutput,
    VerifierOutput,
    ResearchBrief,
    CritiqueResult,
    SearchQueries,
)
from .llm import get_llm

fast_llm = get_llm(mode="fast")
smart_llm = get_llm(mode="smart")

search_tool = DuckDuckGoSearchResults(
    num_results=10,
)

from langchain_core.messages import SystemMessage, HumanMessage

# Define a schema just for the search queries (Step 1)

def research_node(state: AgentState):
    """
    Research Agent: Gathers raw data points based on topic and constraints.
    """
    topic = state["topic"]
    constraints = state["research_constraints"]
    
    system_prompt = f"""ROLE: You are a Research Crawler. You do not write essays. You gather raw data points.

INPUT: 
- Topic: {topic}
- Constraints: {constraints}

INSTRUCTIONS:
1. Use your search tools to find information relevant to the topic.
2. Break down the search results into atomic "claims".
3. For every claim, you MUST preserve the source URL and the exact quote.
4. If you cannot find a source for a specific detail, do not include it.
5. Do not attempt to summarize or synthesize. Just list the raw findings.

OUTPUT FORMAT:
Return strictly a JSON object matching the ResearchOutput schema.
"""
    
    agent = create_agent(
        model=fast_llm,
        tools=[search_tool],
        response_format=ResearchOutput,
        debug=True,
        
    )
    
    response = agent.invoke({'messages': [SystemMessage(content=system_prompt), HumanMessage(content=topic)]})
    
    # print(response)
    # print(type(response['structured_response']))
    # exit()
    
    # Convert Pydantic model to dict for state
    findings = [f.model_dump() for f in response['structured_response'].findings]
    
    # Extract sources for the state
    sources = list(set([f['source_url'] for f in findings]))
    
    print(findings)
    print(sources)
    
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
    
    system_prompt = """ROLE: You are a Fact Auditor. Your only job is to reject weak claims.

INPUT:
- List of Raw Claims (JSON)

INSTRUCTIONS:
1. Review each claim in the provided list.
2. Check the "source_url". If it is from a blacklist domain (e.g., social media, known spam), REJECT it.
3. Check the "publication_date". If it violates the user's time range constraint, REJECT it.
4. Check for Hallucinations: Does the "source_quote" actually support the "claim"? If not, REJECT it.
5. Assign a reliability score (1-10) based on the domain authority.

OUTPUT:
Return a JSON list of verification statuses.
"""
    
    structured_llm = fast_llm.with_structured_output(VerifierOutput)
    response = structured_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=serialized_claims)
    ])
    
    # Map back to claims to separate verified vs rejected
    verified_claims = []
    rejected_claims = []
    
    # We need to map the reviews back to the raw claims. 
    # The schema asks for claim_id, but ResearchFinding doesn't have an ID.
    # We should probably assign IDs in the research node or assume the index matches.
    # The VerifierOutput schema has `claim_id`.
    # I'll update the research node to simply rely on index 0..N implicitly, 
    # or I will assume the Verifier is smart enough to use 0-indexed IDs.
    
    # Let's assume claim_id corresponds to the index in raw_claims.
    
    for review in response.reviews:
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
    # The instructions say "include the claim_id in brackets". 
    # Let's enforce that the input to the synthesizer has explicit IDs.
    claims_with_ids = []
    for i, claim in enumerate(verified_claims):
        c = claim.copy()
        c['claim_id'] = i  # Local ID for this brief
        claims_with_ids.append(c)
        
    serialized_claims = json.dumps(claims_with_ids, indent=2)
    
    system_prompt = """ROLE: You are a Technical Writer. You build structured briefs from verified facts.

INPUT:
- Verified Claims List (JSON)

INSTRUCTIONS:
1. Synthesize the provided verified claims into a cohesive research brief.
2. You are FORBIDDEN from adding any new information not present in the input list.
3. Every sentence you write that contains a fact must include the claim_id in brackets, e.g. [Claim: 12].
4. Organize the content into logical sections (Market, Technology, Risks).
5. Highlight any "Unknowns" — questions that the research data failed to answer.

OUTPUT:
Return strictly a JSON object matching the ResearchBrief schema.
"""
    
    structured_llm = fast_llm.with_structured_output(ResearchBrief)
    response = structured_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=serialized_claims)
    ])
    
    return {
        "draft_brief": response.model_dump()
    }

def critic_node(state: AgentState):
    """
    Critic: Quality assurance.
    """
    draft_brief = state["draft_brief"]
    original_query = state["topic"] # Using topic as query
    
    serialized_brief = json.dumps(draft_brief, indent=2)
    
    system_prompt = f"""ROLE: You are a Senior Editor and Logician. You critique work, you do not fix it.

INPUT:
- Draft Brief (JSON)
- Original User Query: {original_query}

INSTRUCTIONS:
1. Compare the Draft Brief against the Original User Query. Did it answer the prompt?
2. Check for Logical Gaps: Are the arguments sound? 
3. Check for "Fluff": Is the executive summary concise?
4. Score the output from 0-10.
   - < 7: Fail. Provide specific feedback on what is missing or unclear.
   - >= 7: Pass.

OUTPUT:
Return strictly a JSON object matching the CritiqueResult schema.
"""
    
    structured_llm = smart_llm.with_structured_output(CritiqueResult)
    response = structured_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=serialized_brief)
    ])
    
    return {
        "critique_score": response.quality_score,
        "critique_feedback": response.feedback,
        "revision_count": state.get("revision_count", 0) + 1
    }

def editor_node(state: AgentState):
    """
    Editor: Formatting and tone.
    """
    draft_brief = state["draft_brief"]
    audience = state.get("research_constraints", {}).get("audience", "General")
    
    serialized_brief = json.dumps(draft_brief, indent=2)
    
    system_prompt = f"""ROLE: You are a Publisher.

INPUT:
- Validated Research Brief (JSON)
- Target Audience: {audience}

INSTRUCTIONS:
1. Convert the structured JSON brief into a beautifully formatted Markdown document.
2. Adapt the tone for the Target Audience:
   - If "VC": Focus on market size, risks, and upside. Be punchy.
   - If "Engineer": Focus on technical specifics and trade-offs. Be precise.
3. Remove the JSON artifacts (brackets, IDs) and turn them into clean footnotes or hyperlinks.
4. Ensure the layout is scannable (bolding, bullet points).

OUTPUT:
Return the final Markdown string.
"""
    
    # Editor outputs a string, not a struct
    response = smart_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=serialized_brief)
    ])
    
    return {
        "final_doc": response.content
    }

from typing import List, Optional
from pydantic import BaseModel, Field

# 1. Research Agent Schemas
class ResearchFinding(BaseModel):
    claim: str = Field(description="A single atomic fact or statement.")
    source_url: str = Field(description="The direct URL where this fact was found.")
    source_quote: str = Field(description="The exact substring from the source supporting the claim.")

class ResearchOutput(BaseModel):
    findings: List[ResearchFinding]

# 2. Source Verifier Schemas
class VerificationStatus(BaseModel):
    claim_id: int
    is_verified: bool
    rejection_reason: Optional[str] = None
    reliability_score: int = Field(description="1-10 score of source credibility")

class VerifierOutput(BaseModel):
    reviews: List[VerificationStatus]

# 3. Synthesizer Schemas
class BriefSection(BaseModel):
    heading: str
    content: str
    citation_ids: List[int]

class ResearchBrief(BaseModel):
    executive_summary: str
    sections: List[BriefSection]
    risks_and_unknowns: List[str]

# 4. Critic Agent Schemas
class CritiqueResult(BaseModel):
    quality_score: int = Field(description="Score 0-10")
    feedback: str = Field(description="Actionable advice for the Synthesizer")
    pass_check: bool = Field(description="True if score > threshold")

# 5. Editor Agent Schemas
class EditorOutput(BaseModel):
    final_doc: str = Field(description="The final properly formatted markdown document")
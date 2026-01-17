# Project: Autonomous Research & Briefing System (Multi-Agent)

## 1. Core Philosophy & Problem Statement

**The Problem:** Standard LLM research tools fail in three specific areas:

1.  They simply dump links (information overload).
2.  They hallucinate summaries (lack of truth).
3.  They lack accountability (no trail of evidence).

**The Solution:** A multi-agent system based on **Role Separation**, **Strict Verification**, and **Forced Iteration**.

- **differentiation:** This is not standard RAG. Agents have non-overlapping authority, and specific agents (Verifier/Critic) exist solely to block progress until quality thresholds are met.

---

## 2. Agent Architecture

_The system logic relies on distinct agents with restricted scopes._

### A. Research Agent

- **Role:** Information Gatherer.
- **Constraint:** **strictly forbidden from writing prose.**
- **Input:** Topic, Constraints (Time range, depth, domain).
- **Actions:** Search public sources, chunk/embed docs, store raw notes.
- **Output (JSON):**
  ```json
  {
    "claims": ["List of raw facts"],
    "supporting_passages": ["Exact quotes"],
    "source_urls": ["..."],
    "evidence_strength_score": 0.0-1.0
  }
  ```

### B. Source Verifier Agent

- **Role:** Hallucination Control / The Gatekeeper.
- **Constraint:** Exists only to say "No".
- **Actions:** Cross-checks claims against source text. Flags weak/outdated/single-source claims.
- **Output:**
  - Verified Claims List
  - Rejected Claims List (with reasons)
  - Source Reliability Score

### C. Synthesizer Agent

- **Role:** The Writer.
- **Constraint:** Cannot introduce new facts. Must cite Claim IDs.
- **Input:** Verified Claims only.
- **Output Structure:**
  - Executive Summary
  - Key Insights
  - Trade-offs
  - Risks and Unknowns

### D. Critic Agent (The Loop Driver)

- **Role:** Quality Assurance.
- **Actions:** Checks for logical gaps, unanswered questions, and shallow analysis.
- **Logic:** Scores the brief. If `score < threshold` -> **Trigger Re-run** (Force Iteration).
- **Output:** Feedback loop instructions.

### E. Editor Agent

- **Role:** Formatting and Tone.
- **Input:** Target Audience (e.g., Founder, PM, Engineer).
- **Actions:** Improve clarity, remove fluff, preserve facts.

---

## 3. Orchestrator (Non-LLM Control Layer)

_This is a state machine, not a prompt._

**Responsibilities:**

- **Sequencing:** Manages the flow from Research -> Verify -> Synthesize -> Critic.
- **Loop Control:** Handles the "Forced Iteration" triggered by the Critic.
- **Budgets:** Manages time and token limits to prevent infinite loops.
- **Failure Handling:**
  - _Sparse Sources:_ Expand search query.
  - _Conflicting Sources:_ Flag for user review.
  - _Over-iteration:_ Fallback to best available version after N tries.

---

## 4. User Flow & UI Requirements

**Step-by-Step Flow:**

1.  **Input:** User asks: _"Is fine-tuning LLMs still worth it for startups in 2026?"_
2.  **Research:** Agent gathers info (UI updates live progress).
3.  **Verify:** Verifier flags weak claims (UI shows rejected claims in Red).
4.  **Synthesize:** Draft brief created.
5.  **Critique:** Critic rejects draft due to "missing counter-arguments" (UI: "Iteration 2 Triggered").
6.  **Final Output:** Polished brief with citations and confidence score.

**Frontend Elements:**

- Progress timeline (Agent-by-Agent visibility).
- Source Table (Links + Reliability).
- **Rejected Claims View** (Crucial for trust).
- Final Brief with hover-citations.

---

## 5. Technical Stack & Data

- **Backend:** FastAPI (Async tasks for streaming progress).
- **Endpoints:**
  - `POST /brief` (Start job)
  - `GET /brief/{id}/status` (Stream logs/state)
  - `GET /brief/{id}/result` (Final JSON)
- **Internal:** Agent Manager, Vector Store (Chroma/Pinecone), Evidence Registry.
- **Data Sources:** Engineering blogs, documentation, public reports. (No proprietary data required).

---

## 6. Evaluation Metrics

_To distinguish this project from amateur wrappers, we track:_

1.  **Claim Support Rate:** % of final sentences backed by a verified source.
2.  **Iteration Count:** Average cycles required to satisfy the Critic.
3.  **Source Diversity:** Score based on distinct domains used.

---

## 7. Recruiter/Code Reviewer Notes

_Key aspects to highlight in code structure:_

- **Autonomy Boundaries:** Show clear separation of concerns in code modules.
- **Reliability:** Explicit error handling in the Orchestrator.
- **System Thinking:** The architecture is designed as a pipeline, not a single massive prompt.

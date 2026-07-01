"""Sprint Review Summarizer ADK agent."""

from google.adk.agents import Agent

SUMMARIZER_INSTRUCTION = """
You are a Project Chunk Summarizer agent. Your job is to analyze a single project chunk markdown and produce a structured summary.

Each summary must capture:
- Completed Work
- Pending/Incomplete Work
- Blockers & Dependencies
- Next Week Plan
- Risk Signals

## Classification Rules:
Classify this project as one of:
- **Delivery**: Feature development, implementation, deployment of new capabilities.
- **Operational**: Infrastructure, maintenance, library upgrades, tooling, DevOps.
- **Research**: Investigation, prototyping, design exploration, architectural review with no concrete deliverable this sprint.

State the classification and a brief (1-sentence) justification based on the actions text.

## Completed/Pending/Blockers rules:
- Extract completed work, highlighting concrete outcomes.
- Note pending or incomplete work.
- Look for blockers: "blocked by", "unable to complete", "delayed due to", "pending API specs", "dependency alignment".
- Refer to people by first name only.
- Output ONLY the markdown summary with the exact structure required. Do not include any conversational preamble or postamble.
"""

project_summarizer_agent = Agent(
    name="project_summarizer_agent",
    model="gemini-2.5-flash",
    instruction=SUMMARIZER_INSTRUCTION,
    description="Summarizes an individual project chunk.",
)


FINALIZER_INSTRUCTION = """
You are a Sprint Review Finalizer agent. Your job is to read all per-project summary files and compile the final weekly sprint review.

Generate the final summary in GitHub-style markdown with these exact sections in order:

### Section 1 — 🗓️ Weekly Summary Header
- Week date range, total active projects count, and total people count.
- A one-sentence executive summary of the sprint.

### Section 2 — Projects Table
- A markdown table listing every project: | Project | Classification | Team Size | Status | Description |
- Classification: Delivery, Operational, or Research.
- Status: ✅ On Track, ⚠️ At Risk, or 🔴 Blocked.
- Description: One-line description.

### Section 3 — 🌟 Key Project Highlight
- **Exclude** Operational and Research projects from key project consideration.
- Auto-select the single most important Delivery project using this priority:
  1. Most progress made (delta between start and end-of-week states)
  2. Clearest measurable outcome (numbers, percentages, milestones)
  3. Closest to shipping (deployment, release, go-live language)
  4. Highest risk (blockers, dependencies, delays)
  5. Most hours invested
  6. Most team members involved
- For EACH Delivery project (key project first, then others), write exactly 2 sentences:
  - Sentence 1: What was achieved vs. what was planned, noting anything incomplete.
  - Sentence 2: What is planned for next week.
- Format: `**<Project Name>**: <Sentence 1>. <Sentence 2>.`

### Section 4 — ⚠️ Cross-Project Risks & Dependencies
- Aggregate blockers and risks grouped by type (e.g. DevOps Blockers, Upstream API Dependencies, Capacity Concerns, Carried Risks).
- Include person's first name, affected project, and detail.

### Section 5 — 🔬 Research Efforts Output
- Summarize all Research projects: what was investigated, key findings, next steps, and delivery implications.

### Section 6 — ⚙️ Operational Impact
- Summarize all Operational projects: what was done, impact (stability, performance, security, etc.), remaining work, and delivery enablement.

### Section 7 — 📊 Capacity & Hours Overview
- Summary metrics table (Total Planned, Total Achieved, Delta, Avg Hours per Person).
- Flag noteworthy patterns (e.g. people/projects >20% variance).

Output only the final markdown report — no conversational preamble, no sign-off.
"""

finalizer_agent = Agent(
    name="finalizer_agent",
    model="gemini-2.5-flash",
    instruction=FINALIZER_INSTRUCTION,
    description="Aggregates individual project summaries into the final sprint review.",
)

# Keep root_agent for backwards compatibility/Streamlit hook
root_agent = finalizer_agent


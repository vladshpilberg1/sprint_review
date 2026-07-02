"""Sprint Review Summarizer ADK agent.

Agent instructions are loaded directly from the SKILL.md files in
.agents/skills/ so the skills folder is the single source of truth.
"""

from pathlib import Path

from google.adk.agents import Agent

# ---------------------------------------------------------------------------
# Skill loader
# ---------------------------------------------------------------------------

_SKILLS_DIR = Path(__file__).resolve().parent.parent / ".agents" / "skills"


def _load_skill_instruction(skill_name: str) -> str:
    """Read a SKILL.md file and return the body after the YAML frontmatter."""
    skill_path = _SKILLS_DIR / skill_name / "SKILL.md"
    raw = skill_path.read_text(encoding="utf-8")

    # Strip YAML frontmatter (delimited by --- on its own line)
    if raw.startswith("---"):
        end = raw.find("---", 3)
        if end != -1:
            # skip past the closing --- and any immediate newline
            raw = raw[end + 3:].lstrip("\n")

    return raw


# ---------------------------------------------------------------------------
# Agent definitions
# ---------------------------------------------------------------------------

project_summarizer_agent = Agent(
    name="project_summarizer_agent",
    model="gemini-3.5-flash",
    instruction=_load_skill_instruction("sprint-chunk-summarizer"),
    description="Summarizes an individual project chunk.",
)

finalizer_agent = Agent(
    name="finalizer_agent",
    model="gemini-2.5-flash-lite",
    instruction=_load_skill_instruction("sprint-review-finalizer"),
    description="Aggregates individual project summaries into the final sprint review.",
)

# Keep root_agent for backwards compatibility/Streamlit hook
root_agent = finalizer_agent

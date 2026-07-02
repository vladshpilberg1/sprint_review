# Sprint Review System

An end-to-end sprint management platform powered by **Google ADK** (Agent Development Kit) and **Streamlit**. The system has two main workflows:

1. **Data Collection** — An AI-guided interview bot gathers weekly sprint progress from each team member and compiles the responses into a standardised CSV.
2. **Review Summariser** — Uploads a work-planning CSV, slices it into per-project chunks, summarises each project with an LLM, and produces a polished 7-section sprint review report.

Both apps share a common security layer that scrubs PII and blocks prompt-injection attempts before any text reaches an LLM.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the Apps](#running-the-apps)
- [CSV Format](#csv-format)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [ADK Skills Pipeline](#adk-skills-pipeline)
- [Security Layer](#security-layer)
- [Configuration](#configuration)

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| pip | latest |
| Google AI Studio API key | [Get one here](https://aistudio.google.com/apikey) |

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd sprint_review
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `google-adk` — Google Agent Development Kit
- `streamlit` — Web UI framework
- `python-dotenv` — `.env` file loading
- `pandas` — CSV parsing and data manipulation

### 4. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and set your Google AI Studio API key:

```env
GOOGLE_API_KEY=your_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=False
```

> **Note:** Set `GOOGLE_GENAI_USE_VERTEXAI=True` if you want to use Vertex AI instead of AI Studio.

---

## Running the Apps

### Sprint Data Collection (Interview Bot)

Collects sprint progress from team members through an AI-guided conversational interview.

```bash
streamlit run streamlit_collect.py
```

Opens at `http://localhost:8501`. Workflow:

1. Select your name, reporting week (Friday), and the projects you worked on.
2. Click **Start Interview** — the AI agent asks about each project one at a time.
3. For each project, provide: planned work & hours, achieved work & hours, dependencies, and next-week plans.
4. The agent confirms details and outputs a structured JSON summary.
5. Once all team members have submitted, click **Compile Selected Week** to generate a CSV.
6. Download the compiled CSV for use in the Review Summariser.

### Sprint Review Summariser

Generates a polished sprint review report from a work-planning CSV.

```bash
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501` (use a different port if both apps run simultaneously — Streamlit auto-assigns `8502`). Workflow:

1. Upload a work-planning CSV (either compiled from the Data Collection app or manually created).
2. Preview the parsed data with project type badges.
3. Click **Generate Summary** — the 3-phase pipeline runs:
   - **Phase 1:** Slices the CSV into per-project markdown chunks.
   - **Phase 2:** Summarises each project chunk with the LLM (sequential to respect rate limits).
   - **Phase 3:** Aggregates all summaries into the final 7-section report.
4. View and download the report as Markdown.

---

## CSV Format

The work-planning CSV supports an optional **type-header row** above the column headers:

### With type headers (recommended)

```
,,, Refinement, Refinement, Delivery, Delivery, Operations, Operations
Assignee, Plan, Hours, Eval Suite, Prompt Migration, Tyrell Corp, Buy N Large, Code Coverage >90%, Test Automation
Alex, 7/3 Plan - Actions,, Resolve issues...,, Write unit tests...,,,
Alex, 7/3 Plan - Hours, 40, 26,,14,,,
...
```

### Without type headers (basic)

```
Assignee, Plan, Hours, Project 1, Project 2, Project 3
Alex, 7/3 Plan - Actions,, Resolve issues...,, Write unit tests...
Alex, 7/3 Plan - Hours, 40, 26,, 14
...
```

### Row structure per person

Each team member has **6 rows** per reporting cycle:

| Row | Description |
|-----|-------------|
| `<week> Plan - Actions` | What was planned for this week |
| `<week> Plan - Hours` | Planned hours per project (total in Hours column) |
| `<week> Achieved - Actions` | What was actually completed |
| `<week> Achieved - Hours` | Actual hours spent per project |
| `<next week> Plan - Actions` | Plan for next week |
| `<next week> Plan - Hours` | Planned hours for next week |

Blank separator rows between team members are optional.

> **Date convention:** All dates in the CSV represent **Fridays**. The system derives the work week as Monday (Friday − 4 days) through Friday.

---

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐
│  streamlit_collect   │     │   streamlit_app      │
│  (Data Collection)   │     │  (Review Summariser) │
│                      │     │                      │
│  AI Interview Bot    │     │  CSV Upload + Preview│
│  → JSON per user     │     │  → 3-Phase Pipeline  │
│  → Compile CSV       │     │  → Markdown Report   │
└──────────┬───────────┘     └──────────┬───────────┘
           │                            │
     ┌─────▼────────────────────────────▼─────┐
     │           Security Layer               │
     │  PII Scrubbing · Injection Defence     │
     └────────────────┬───────────────────────┘
                      │
     ┌────────────────▼───────────────────────┐
     │          Google ADK Agents             │
     │                                        │
     │  data_collection_agent (interview)     │
     │  project_summarizer_agent (per-chunk)  │
     │  finalizer_agent (final report)        │
     └────────────────┬───────────────────────┘
                      │
     ┌────────────────▼───────────────────────┐
     │        Gemini / Gemma Models           │
     │  (via Google AI Studio or Vertex AI)   │
     └────────────────────────────────────────┘
```

---

## Project Structure

```
sprint_review/
├── app/
│   ├── __init__.py               # Package init — exports root_agent
│   ├── agent.py                  # ADK agent definitions (summariser + finaliser)
│   ├── csv_compiler.py           # Compiles interview JSON into work-planning CSV
│   ├── data_collection_agent.py  # AI interview agent for sprint data collection
│   ├── security.py               # PII scrubbing + prompt-injection defence
│   └── tools.py                  # CSV parsing, type detection, chunk extraction
│
├── .agents/
│   └── skills/
│       ├── sprint-chunk-extractor/
│       │   └── SKILL.md          # Skill 1: Split CSV → per-project chunks
│       ├── sprint-chunk-summarizer/
│       │   └── SKILL.md          # Skill 2: Summarise each project chunk
│       └── sprint-review-finalizer/
│           └── SKILL.md          # Skill 3: Aggregate into final report
│
├── streamlit_app.py              # UI: Sprint Review Summariser
├── streamlit_collect.py          # UI: Sprint Data Collection (Interview Bot)
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── .gitignore
└── README.md
```

---

## ADK Skills Pipeline

The review summariser uses a 3-stage pipeline, each powered by its own ADK skill:

### Stage 1 — Chunk Extractor

Slices the CSV into one markdown file per active project, containing only the relevant rows and columns.

- **Input:** Raw CSV content
- **Output:** Per-project markdown chunks
- **Agent:** `extract_project_chunks()` in `app/tools.py` (Python, no LLM needed)

### Stage 2 — Chunk Summariser

Reads each project chunk and produces a structured summary with: completed work, pending work, blockers & dependencies, next-week plans, and risk signals.

- **Input:** One project chunk (markdown)
- **Output:** Structured project summary
- **Agent:** `project_summarizer_agent` (LLM-powered)
- **Model:** `gemma-4-31b-it` (configurable in `app/agent.py`)

### Stage 3 — Review Finaliser

Aggregates all per-project summaries into a polished 7-section sprint review report.

- **Input:** All project summaries combined
- **Output:** Final sprint review document with:
  1. Weekly Summary Header
  2. Projects Table
  3. Key Project Highlight
  4. Cross-Project Risks & Dependencies
  5. Research Efforts Output
  6. Operational Impact
  7. Capacity & Hours Overview
- **Agent:** `finalizer_agent` (LLM-powered)
- **Model:** `gemma-4-31b-it` (configurable in `app/agent.py`)

---

## Security Layer

All user-supplied text passes through `app/security.py` before reaching any LLM. The pipeline runs in two stages:

### PII Scrubbing

Detects and replaces sensitive information with safe placeholders:

| PII Type | Example | Replacement |
|----------|---------|-------------|
| Email addresses | `user@example.com` | `[EMAIL_REDACTED]` |
| Employee IDs | `EMP-12345` | `[EMPLOYEE_ID_REDACTED]` |
| SSNs | `123-45-6789` | `[SSN_REDACTED]` |
| Credit card numbers | `4111-1111-1111-1111` | `[CC_REDACTED]` |

### Prompt Injection Defence

Detects and strips common injection patterns including:
- "Ignore previous instructions" variants
- Role-hijacking attempts ("you are now a…")
- Chat-template injection markers (`<|im_start|>`, `[INST]`, etc.)
- Instruction override attempts

Both stages are pure-Python (regex-based) with zero external dependencies, adding no latency or API cost.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | — | Your Google AI Studio API key |
| `GOOGLE_GENAI_USE_VERTEXAI` | No | `False` | Set to `True` to use Vertex AI instead of AI Studio |

### Model Selection

Models are configured in [`app/agent.py`](app/agent.py) and [`app/data_collection_agent.py`](app/data_collection_agent.py). Current defaults:

| Agent | Model | Purpose |
|-------|-------|---------|
| `project_summarizer_agent` | `gemma-4-31b-it` | Per-project chunk summarisation |
| `finalizer_agent` | `gemma-4-31b-it` | Final report generation |
| `data_collection_agent` | `gemini-2.5-flash-lite` | Sprint interview conversations |

To change a model, edit the `model=` parameter in the agent definition.

### Hardcoded Constants

The data collection app (`streamlit_collect.py`) has team and project configuration defined as constants:

- **`USERS`** — List of team member names
- **`PROJECTS`** — Dictionary mapping project names to type labels (`Refinement`, `Delivery`, `Operations`)

Update these at the top of `streamlit_collect.py` to match your team.

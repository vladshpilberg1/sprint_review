# Sprint Review Summarizer

A Streamlit web app that accepts a work-planning CSV and uses a **Google ADK** agent to generate a structured weekly sprint summary.

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your API key

```bash
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY to your AI Studio key
# Get one at: https://aistudio.google.com/apikey
```

### 4. Run the app

```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`.

---

## CSV Format

| Assignee | Plan | Hours | Project 1 | Project 2 | Project 3 |
|---|---|---|---|---|---|
| Alex | 6/26 Plan - Actions | | Resolve issues... | | Write unit tests... |
| Alex | 6/26 Plan - Hours | 40 | 26 | | 14 |
| Alex | 6/26 Achieved - Actions | | Upgraded libraries... | | Completed... |
| ... | ... | ... | ... | ... | ... |

Each person should have rows for:
- `<week> Plan - Actions` / `<week> Plan - Hours`
- `<week> Achieved - Actions` / `<week> Achieved - Hours`
- `<next week> Plan - Actions` / `<next week> Plan - Hours`

---

## Project Structure

```
sprint_review/
├── app/
│   ├── __init__.py       # Package init
│   ├── agent.py          # ADK LlmAgent definition
│   └── tools.py          # parse_csv_data tool
├── .agents/
│   └── skills/
│       └── sprint-review-summarizer/
│           └── SKILL.md  # Reusable ADK skill prompt
├── streamlit_app.py      # Streamlit UI
├── requirements.txt
├── .env.example
└── README.md
```

## ADK Skill

The summary logic is encoded as a reusable workspace skill at
`.agents/skills/sprint-review-summarizer/SKILL.md`.
Any ADK agent or Antigravity coding session in this workspace can load it.

---
name: sprint-chunk-extractor
description: >
  Use this skill when you need to split a work-planning CSV into
  per-project chunk files. It reads the CSV, identifies all project columns,
  and writes one markdown chunk file per active project containing only
  the relevant rows and columns. Output goes to
  sprint_review_results/chunks/. Run this BEFORE sprint-chunk-summarizer.
---

# Sprint Chunk Extractor

## Purpose

Parse a work-planning CSV and produce one self-contained markdown chunk
file per project. Each chunk contains **only** the rows and columns
relevant to that project, so downstream summarisation can operate on a
minimal context window.

## Input

A CSV file with these columns:

```
Assignee, Plan, Hours, Project 1, Project 2, …, Project N
```

Each person has rows for:
- `<week> Plan - Actions`   — what was planned
- `<week> Plan - Hours`     — planned hours per project
- `<week> Achieved - Actions` — what was actually done
- `<week> Achieved - Hours`   — actual hours per project
- `<next week> Plan - Actions` — next week's plan
- `<next week> Plan - Hours`   — next week's planned hours

## Procedure

1. **Read the CSV** provided by the user (file path or pasted content).
2. **Identify the week date range** from the Plan row labels
   (e.g. "6/26 Plan - Actions" → week of June 26; "7/3 Plan - Actions" → next week is July 3).
3. **Identify project columns** — every column after `Hours`.
4. **For each project column**, check if any person has non-empty action
   or hours data. If the entire column is blank, skip that project.
5. **For each active project**, create a chunk file with the structure
   defined below.
6. **Write a manifest** file summarising all chunks created.

## Chunk File Format

Write each chunk to: `sprint_review_results/chunks/<project_name_slug>.md`

Where `<project_name_slug>` is the column name lowercased with spaces
replaced by underscores (e.g. "Project 1" → `project_1`).

Each chunk file must follow this structure:

```markdown
# <Project Name>

- **Week**: <date range, e.g. June 26 – July 2, 2026>
- **Assignees**: <comma-separated list of people who have data for this project>

## Assignee Details

### <Assignee Name>

| Row Type | Action | Hours |
|----------|--------|-------|
| <week> Plan - Actions | <action text or "—"> | <hours or "—"> |
| <week> Achieved - Actions | <action text or "—"> | <hours or "—"> |
| <next week> Plan - Actions | <action text or "—"> | <hours or "—"> |

---
```

Repeat the assignee table for each person who has data for this project.

## Manifest File

Write the manifest to: `sprint_review_results/chunks/_manifest.md`

```markdown
# Chunk Manifest

- **Source CSV**: <filename>
- **Week**: <date range>
- **Total active projects**: <count>
- **Total assignees across all projects**: <count>

## Chunks

| # | Project | Assignees | Chunk File |
|---|---------|-----------|------------|
| 1 | Project 1 | Alice, Bob | project_1.md |
| 2 | Project 4 | Dan, Harold | project_4.md |
| … | … | … | … |
```

## Rules

- Never invent data not present in the CSV.
- If a cell is empty, write "—" in the chunk table.
- Refer to people by their first name only.
- Create the `sprint_review_results/chunks/` directory if it does not exist.
- Overwrite any existing chunk files from a previous run.
- Only include projects that have at least one non-empty action or hours
  entry across all assignees.

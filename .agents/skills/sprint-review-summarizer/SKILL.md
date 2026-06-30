---
name: sprint-review-summarizer
description: >
  Use this skill when you need to generate a sprint review summary from a
  work-planning CSV. It produces: a project count, a key-project highlight
  (2 sentences: what was achieved and what is planned next week), and a
  dependencies/delays section. The key project is auto-selected based on
  team breadth, measurable outcomes, and business signal (nearest to
  shipping or highest-risk blockers).
---

# Sprint Review Summarizer

## Purpose

Generate a structured weekly sprint summary from a work-planning CSV that
has the following columns:

```
Assignee, Plan, Hours, Project 1, Project 2, Project 3, ...
```

Each person has rows for:
- `<week> Plan - Actions`   — what was planned
- `<week> Plan - Hours`     — planned hours per project
- `<week> Achieved - Actions` — what was actually done
- `<week> Achieved - Hours`   — actual hours per project
- `<next week> Plan - Actions` — next week's plan
- `<next week> Plan - Hours`   — next week's planned hours

## Output Format
Save the output to a markdown file named sprint_summary[<week_date>].md in the sprint_review_results direcory.

Produce the summary in **GitHub-style markdown** with these sections:

### 1. Weekly Summary Header
State the week date range (infer from the Plan row labels) and the total
number of distinct projects worked on.

### 2. Projects Table
A markdown table listing each project column name and a one-line description
inferred from the actions text.

### 3. Key Project Highlight
**Auto-select** the key project using this priority order:
1. Most team members involved
2. Clearest measurable outcome (numbers, percentages, milestones)
3. Closest to shipping (deployment, release, go-live language)
4. Active blocker or highest risk

Write exactly **2 sentences**:
- Sentence 1: What was achieved this week.
- Sentence 2: What is planned for next week.

### 4. Dependencies & Delays
A bulleted list of any blockers, dependencies on other teams, or work that
could not be completed. Include the person's name, what was blocked, and
the reason. If none, write "No blockers reported."

## Rules
- Never invent data not present in the CSV.
- If a cell is empty, treat it as "no action / no hours".
- Refer to people by their first name only.
- Use emoji sparingly: 🗓️ for the header, 🌟 for the key project, ⚠️ for blockers.

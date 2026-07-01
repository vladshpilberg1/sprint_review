"""Tools for the Sprint Review Summarizer agent."""

import io
import pandas as pd


def parse_csv_data(csv_content: str) -> dict:
    """Parse a work-planning CSV and return a structured text representation.

    The CSV must have columns: Assignee, Plan, Hours, and one or more Project
    columns. Each person has rows for planned actions, planned hours, achieved
    actions, achieved hours, and next-week plan.

    Args:
        csv_content: Raw CSV file content as a string.

    Returns:
        dict with 'status' and 'data' keys. 'data' is a human-readable
        markdown table and row-by-row breakdown ready for the LLM to analyse.
    """
    try:
        df = pd.read_csv(io.StringIO(csv_content))

        # Drop fully empty rows
        df = df.dropna(how="all")

        # Identify project columns (everything after 'Hours')
        fixed_cols = ["Assignee", "Plan", "Hours"]
        project_cols = [c for c in df.columns if c not in fixed_cols]

        if not project_cols:
            return {
                "status": "error",
                "message": "No project columns found. Expected columns after 'Hours'.",
            }

        lines: list[str] = []
        lines.append(f"## Projects detected: {', '.join(project_cols)}\n")

        # Group by assignee and emit a readable block per person
        assignees = df["Assignee"].dropna().unique()
        for assignee in assignees:
            person_rows = df[df["Assignee"] == assignee]
            lines.append(f"### {assignee}")
            for _, row in person_rows.iterrows():
                plan_label = str(row.get("Plan", "")).strip()
                hours = str(row.get("Hours", "")).strip()
                hour_part = f" (Total: {hours}h)" if hours and hours != "nan" else ""
                lines.append(f"**{plan_label}**{hour_part}")
                for proj in project_cols:
                    val = str(row.get(proj, "")).strip()
                    if val and val.lower() not in ("nan", ""):
                        lines.append(f"  - {proj}: {val}")
            lines.append("")

        return {"status": "success", "data": "\n".join(lines)}

    except Exception as exc:  # pylint: disable=broad-except
        return {"status": "error", "message": str(exc)}


def extract_project_chunks(csv_content: str) -> dict:
    """Parse a work-planning CSV and extract individual markdown chunks per active project.

    Args:
        csv_content: Raw CSV file content as a string.

    Returns:
        dict mapping project column names (e.g. "Project 1") to markdown chunk strings.
    """
    df = pd.read_csv(io.StringIO(csv_content))
    df = df.dropna(how="all")

    fixed_cols = ["Assignee", "Plan", "Hours"]
    project_cols = [c for c in df.columns if c not in fixed_cols]

    # Clean plan labels to find week
    all_plans = df["Plan"].dropna().unique()
    week_str = "Unknown Week"
    for plan in all_plans:
        if "Plan - Actions" in plan:
            week_str = f"Week of {plan.split(' ')[0]}"
            break

    chunks = {}

    for proj in project_cols:
        # Check if project has any non-empty actions or hours
        proj_rows = df[df[proj].notna() & (df[proj].astype(str).str.strip() != "") & (df[proj].astype(str).str.strip().str.lower() != "nan")]
        if proj_rows.empty:
            continue

        # Get list of unique assignees who worked on this project
        assignees = proj_rows["Assignee"].dropna().unique()
        if len(assignees) == 0:
            continue

        chunk_lines = []
        chunk_lines.append(f"# {proj}\n")
        chunk_lines.append(f"- **Week**: {week_str}")
        chunk_lines.append(f"- **Assignees**: {', '.join(assignees)}\n")
        chunk_lines.append("## Assignee Details\n")

        for assignee in assignees:
            # We want all rows for this assignee where they had entries for this project
            person_rows = df[df["Assignee"] == assignee]
            
            chunk_lines.append(f"### {assignee}\n")
            chunk_lines.append("| Row Type | Action | Hours |")
            chunk_lines.append("|----------|--------|-------|")

            for _, row in person_rows.iterrows():
                plan_label = str(row.get("Plan", "")).strip()
                val = str(row.get(proj, "")).strip()
                hours = str(row.get("Hours", "")).strip()
                
                # Check if it's actions or hours row
                row_type = "Actions" if "Actions" in plan_label else "Hours" if "Hours" in plan_label else "Unknown"
                
                if val and val.lower() not in ("nan", ""):
                    # Let's present action/hours nicely
                    if row_type == "Actions":
                        chunk_lines.append(f"| {plan_label} | {val} | — |")
                    elif row_type == "Hours":
                        chunk_lines.append(f"| {plan_label} | — | {val} |")
                else:
                    chunk_lines.append(f"| {plan_label} | — | — |")
            chunk_lines.append("")

        chunks[proj] = "\n".join(chunk_lines)

    return chunks


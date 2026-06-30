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

"""CSV compiler — assembles collected sprint submissions into the work-planning CSV format.

Target format (matching the existing template):

    Assignee,Plan,Hours,<Project A>,<Project B>,...
    Alex,7/3 Plan - Actions,,<actions>,<actions>,...
    Alex,7/3 Plan - Hours,40,20,20,...
    Alex,7/3 Achieved - Actions,,<actions>,<actions>,...
    Alex,7/3 Achieved - Hours,40,22,18,...
    Alex,7/10 Plan - Actions,,<actions>,<actions>,...
    Alex,7/10 Plan - Hours,40,24,16,...
    <blank separator row>
    Bob,...
"""

from __future__ import annotations

import csv
import io
from datetime import date, timedelta


def compile_week_csv(
    submissions: dict[tuple[str, date], dict],
    target_friday: date,
    all_projects: list[str],
) -> str | None:
    """Compile all user submissions for *target_friday* into a CSV string.

    Args:
        submissions: Mapping of ``(user_name, friday_date)`` → parsed JSON
            dict with a ``"projects"`` list (as produced by the data-collection
            agent).
        target_friday: The Friday that identifies the reporting week.
        all_projects: Master list of project names used for consistent column
            ordering.

    Returns:
        A CSV string ready for download, or ``None`` if no submissions exist
        for the requested week.
    """
    # ── Gather data for the target week ──────────────────────────────────
    week_data: dict[str, dict] = {}
    active_projects: set[str] = set()

    for (user, friday), data in submissions.items():
        if friday == target_friday:
            week_data[user] = data
            for proj in data.get("projects", []):
                active_projects.add(proj["name"])

    if not week_data:
        return None

    # Column order follows the master project list
    ordered_projects = [p for p in all_projects if p in active_projects]

    # ── Date labels ──────────────────────────────────────────────────────
    date_str = f"{target_friday.month}/{target_friday.day}"
    next_friday = target_friday + timedelta(weeks=1)
    next_date_str = f"{next_friday.month}/{next_friday.day}"

    # ── Build CSV ────────────────────────────────────────────────────────
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")

    # Header
    writer.writerow(["Assignee", "Plan", "Hours"] + ordered_projects)

    users = sorted(week_data.keys())
    for user_idx, user in enumerate(users):
        proj_map = {
            p["name"]: p for p in week_data[user].get("projects", [])
        }

        # ---- Row 1: Plan – Actions ----
        row: list = [user, f"{date_str} Plan - Actions", ""]
        for proj in ordered_projects:
            p = proj_map.get(proj)
            row.append(p["plan_actions"] if p else "")
        writer.writerow(row)

        # ---- Row 2: Plan – Hours ----
        hours = [
            proj_map[proj]["plan_hours"] if proj in proj_map else 0
            for proj in ordered_projects
        ]
        total = sum(h for h in hours if h)
        row = [user, f"{date_str} Plan - Hours", total if total else ""]
        for h in hours:
            row.append(h if h else "")
        writer.writerow(row)

        # ---- Row 3: Achieved – Actions ----
        row = [user, f"{date_str} Achieved - Actions", ""]
        for proj in ordered_projects:
            p = proj_map.get(proj)
            row.append(p["achieved_actions"] if p else "")
        writer.writerow(row)

        # ---- Row 4: Achieved – Hours ----
        hours = [
            proj_map[proj]["achieved_hours"] if proj in proj_map else 0
            for proj in ordered_projects
        ]
        total = sum(h for h in hours if h)
        row = [user, f"{date_str} Achieved - Hours", total if total else ""]
        for h in hours:
            row.append(h if h else "")
        writer.writerow(row)

        # ---- Row 5: Next-week Plan – Actions ----
        row = [user, f"{next_date_str} Plan - Actions", ""]
        for proj in ordered_projects:
            p = proj_map.get(proj)
            row.append(p.get("next_week_actions", "") if p else "")
        writer.writerow(row)

        # ---- Row 6: Next-week Plan – Hours ----
        hours = [
            proj_map[proj].get("next_week_hours", 0) if proj in proj_map else 0
            for proj in ordered_projects
        ]
        total = sum(h for h in hours if h)
        row = [user, f"{next_date_str} Plan - Hours", total if total else ""]
        for h in hours:
            row.append(h if h else "")
        writer.writerow(row)

        # Blank separator row (except after the last user)
        if user_idx < len(users) - 1:
            writer.writerow([""] * (3 + len(ordered_projects)))

    return buf.getvalue()

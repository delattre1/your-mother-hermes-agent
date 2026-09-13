"""The weekly recap, pure: seven days in, one verdict out."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from mother.engine.streak import best_streak_between
from mother.models import Status, Task


def weekly(tasks: list[Task], today: date, days: int = 7) -> dict[str, Any]:
    start = today - timedelta(days=days - 1)
    rows = []
    for task in tasks:
        counts = {str(Status.DONE): 0, str(Status.SKIPPED): 0, str(Status.MISS): 0}
        day = start
        while day <= today:
            entry = task.entry_for(day.isoformat())
            if entry is not None:
                counts[entry.get("status", str(Status.MISS))] += 1
            day += timedelta(days=1)
        rows.append({
            "id": task.id,
            "name": task.name,
            "feito": counts[str(Status.DONE)],
            "pulou": counts[str(Status.SKIPPED)],
            "faltas": counts[str(Status.MISS)],
            "best_streak": best_streak_between(task, start, today),
        })
    worst = max(rows, key=lambda row: (row["faltas"], -row["feito"]), default=None)
    return {
        "from": start.isoformat(), "to": today.isoformat(), "days": days,
        "tasks": rows,
        "worst": {"id": worst["id"], "name": worst["name"], "faltas": worst["faltas"]} if worst else None,
        "no_tasks": not tasks,
    }

"""The nightly checkup, pure: the state of every chore on one date. The cron
turn reads it and speaks; the escalation rule lives here so tests can prove
the photo gets asked exactly when the misses say it must."""

from __future__ import annotations

from datetime import date
from typing import Any

from mother.engine.streak import consecutive_misses, current_streak
from mother.models import Status, Task


def build(tasks: list[Task], today: date, proof_after: int = 3) -> dict[str, Any]:
    """One JSON object: today's per-task state, pending ids, escalation."""
    rows: list[dict[str, Any]] = []
    for task in tasks:
        entry = task.entry_for(today.isoformat())
        misses = consecutive_misses(task, today)
        status = entry.get("status") if entry else None
        # Escalation counts TODAY's miss: a third unanswered night is a photo
        # request, not a third identical question.
        pending_misses = misses + (1 if status is None else 0)
        rows.append({
            "id": task.id,
            "name": task.name,
            "status": status,
            "motivo": entry.get("motivo") if entry else None,
            "streak": current_streak(task, today),
            "consecutive_misses": misses,
            "need_photo": pending_misses >= max(1, proof_after),
            "answered": entry is not None,
        })
    pending = [row["id"] for row in rows if row["status"] is None]
    return {
        "date": today.isoformat(),
        "tasks": rows,
        "pending": pending,
        "all_done": bool(tasks) and not pending,
        "no_tasks": not tasks,
    }


def mark_missed(tasks: list[Task], today: date) -> list[str]:
    """Tasks with no answer today become confirmed misses. The checkup cron
    calls this once, right before speaking -- a day with no word is a day
    charged. Returns the ids it charged, so the caller never guesses."""
    charged = []
    for task in tasks:
        if task.entry_for(today.isoformat()) is None:
            task.set_entry(today.isoformat(), Status.MISS)
            charged.append(task.id)
    return charged

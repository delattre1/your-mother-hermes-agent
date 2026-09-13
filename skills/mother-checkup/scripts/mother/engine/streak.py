"""Streak math, pure: dates in, numbers out. No clock reads, no IO."""

from __future__ import annotations

from datetime import date, timedelta

from mother.models import Status, Task


def current_streak(task: Task, today: date) -> int:
    """Consecutive done days ending today or yesterday. A gap (no entry) is
    not a miss the user owed an answer for -- it breaks the count rather than
    counting against it."""
    streak = 0
    day = today
    if task.entry_for(day.isoformat()) is None:
        day -= timedelta(days=1)
    while (entry := task.entry_for(day.isoformat())) is not None:
        if entry.get("status") != str(Status.DONE):
            break
        streak += 1
        day -= timedelta(days=1)
    return streak


def consecutive_misses(task: Task, today: date) -> int:
    """Trailing confirmed misses -- days the checkup ran and no answer came.
    Today still open counts through yesterday: the ledger charges closed
    days, and the open one is what the escalation adds on top. A skip with
    a reason is an answer, not a miss, and breaks the chain."""
    misses = 0
    day = today
    if task.entry_for(day.isoformat()) is None:
        day -= timedelta(days=1)
    while (entry := task.entry_for(day.isoformat())) is not None:
        if entry.get("status") != str(Status.MISS):
            break
        misses += 1
        day -= timedelta(days=1)
    return misses


def best_streak_between(task: Task, start: date, end: date) -> int:
    """The longest run of done days inside the window, inclusive."""
    best = run = 0
    day = start
    while day <= end:
        entry = task.entry_for(day.isoformat())
        if entry is not None and entry.get("status") == str(Status.DONE):
            run += 1
            best = max(best, run)
        else:
            run = 0
        day += timedelta(days=1)
    return best

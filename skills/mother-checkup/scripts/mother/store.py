"""The task store: one JSON file, written whole, keyed by stable slug."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from kit.jsonio import load_json, save_json_atomic

from mother.models import Status, Task

_TASKS_FILE = "tasks.json"


def tasks_path(home: str) -> str:
    return f"{home}/{_TASKS_FILE}"


def task_id_for(name: str) -> str:
    """A stable slug: 'Arrumar o quarto' and 'arrumar o quarto' are one task."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


class MotherStore:
    """The chores and their history, loaded once, written whole."""

    def __init__(self, home: str) -> None:
        self.home = home
        raw = load_json(tasks_path(home), {"tasks": []}) or {}
        self.tasks: dict[str, Task] = {
            data["id"]: Task.from_dict(data) for data in raw.get("tasks", [])
        }

    def save(self) -> None:
        save_json_atomic(tasks_path(self.home),
                         {"tasks": [task.as_dict() for task in self.tasks.values()]})

    def add(self, name: str, created_at: str) -> Task:
        """One task per slug: adding twice answers where it is, never errors."""
        task_id = task_id_for(name)
        if task_id in self.tasks:
            return self.tasks[task_id]
        task = Task(id=task_id, name=name.strip(), created_at=created_at)
        self.tasks[task_id] = task
        return task

    def remove(self, task_id: str) -> Task:
        return self.tasks.pop(task_id)

    def all(self) -> list[Task]:
        return sorted(self.tasks.values(), key=lambda task: task.created_at)

    def get(self, ref: str) -> Task:
        """Find a task by id or by name, case-insensitive. Exact id wins."""
        if ref in self.tasks:
            return self.tasks[ref]
        wanted = ref.strip().lower()
        for task in self.tasks.values():
            if task.name.lower() == wanted:
                return task
        raise KeyError(f"no task named {ref!r}")

    def set_status(self, task: Task, date_iso: str, status: Status,
                   motivo: str | None = None) -> Task:
        """What the user said happened today. A later word overwrites an
        earlier one on the same day -- charged at 21:00, done at 22:00 still
        counts, and the entry says the correction happened."""
        task.set_entry(date_iso, status, motivo)
        self.save()
        return task

    def compact_view(self, task: Task) -> dict[str, Any]:
        return {"id": task.id, "name": task.name, "created_at": task.created_at,
                "days_tracked": len(task.history)}

"""The data model: chores and what happened to them, day by day. Serialization
is explicit -- the store file is a contract, not a dict dump.

The model records what the user SAID happened. It never claims to know what
actually happened: the engine has no eyes, and the day the photo says
otherwise, the entry is a lie on record, not a fact the engine endorsed."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Status(StrEnum):
    DONE = "feito"      # the user said it was done
    SKIPPED = "pulou"   # the user said it was not, and why
    MISS = "falta"      # checkup ran, no answer came


@dataclass
class Task:
    """One chore, charged every day until removed."""

    id: str                          # stable slug ("arrumar-o-quarto")
    name: str
    created_at: str                  # ISO instant
    history: dict[str, dict[str, Any]] = field(default_factory=dict)
    # history: date iso -> {"status": Status, "motivo": str | None}

    def entry_for(self, date_iso: str) -> dict[str, Any] | None:
        return self.history.get(date_iso)

    def set_entry(self, date_iso: str, status: Status, motivo: str | None = None) -> None:
        self.history[date_iso] = {"status": str(status), "motivo": motivo}

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "created_at": self.created_at,
                "history": self.history}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Task":
        return cls(id=raw["id"], name=raw["name"], created_at=raw["created_at"],
                   history=dict(raw.get("history", {})))

"""Agent preferences. Missing keys mean onboarding is unfinished; the cron
schedules live here so onboarding can register exactly what the user chose."""

from __future__ import annotations

from typing import Any

from kit.jsonio import load_json, save_json_atomic

REQUIRED_KEYS = ("timezone", "checkup_time", "language")

DEFAULTS: dict[str, Any] = {
    "timezone": "UTC",
    "checkup_time": "21:30",          # informational: the schedule below is law
    "checkup_schedule": "30 21 * * *",
    "recap_schedule": "0 20 * * 0",   # Sunday
    "checkup_enabled": True,
    "language": "",                   # "" = mirror the user each turn
    "proof_after": 3,                 # consecutive misses before a photo is asked
    "cron_registered": False,
}

# The default charge. The user's own list replaces it at onboarding -- or
# confirms it, because these four are what a house runs on.
SEED_TASKS = ["lavar louça", "jogar o lixo fora", "arrumar o quarto", "treinar"]


def config_path(home: str) -> str:
    return f"{home}/config.json"


def load(home: str) -> dict[str, Any]:
    stored = load_json(config_path(home), {}) or {}
    return {**DEFAULTS, **stored}


def save(home: str, config: dict[str, Any]) -> None:
    save_json_atomic(config_path(home), config)


def missing_keys(home: str) -> list[str]:
    """Keys onboarding has not asked about yet -- judged on the FILE, never on
    the defaults: a default is what the agent runs on, not what the user chose."""
    stored = load_json(config_path(home), {}) or {}
    return [key for key in REQUIRED_KEYS if key not in stored]

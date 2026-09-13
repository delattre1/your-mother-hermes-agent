#!/usr/bin/env python3
"""mother.py -- the chore ledger. One JSON object per command, 0/1/2 on exit.

    tasks list                        everything, compact
    tasks add <name...>               one task per slug; twice is a no-op
    tasks seed                        the default four, where missing
    tasks remove <id>                 stop charging it
    done <id|name> [--note ...]       the user says it was done
    skip <id|name> --motivo ...       the user says it was not, and why
    checkup [--mark-missed]           today's state; the cron marks, chat asks
    recap [--days N]                  the last N days, one verdict
    config get [key] | set k v        preferences the onboarding wrote

Dates come from the config's timezone, never from the shell's -- the day
boundary is the user's, not the container's."""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from kit import clock  # noqa: E402

from mother import config as config_module  # noqa: E402
from mother import store as store_module  # noqa: E402
from mother.engine import checkup as checkup_module  # noqa: E402
from mother.engine import recap as recap_module  # noqa: E402
from mother.models import Status  # noqa: E402
from mother.store import MotherStore  # noqa: E402


def emit(payload: object, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def fail(message: str, code: int = 2) -> int:
    return emit({"error": message}, code)


def home() -> str:
    return os.environ.get("MOTHER_HOME") or "/var/lib/hermes/mother"


def today_iso(store_home: str) -> str:
    zone = config_module.load(store_home)["timezone"]
    return clock.now(zone).date().isoformat()


def cmd_tasks(args: argparse.Namespace) -> int:
    store = MotherStore(home())
    if args.action == "list":
        return emit({"tasks": [store.compact_view(t) for t in store.all()]})
    if args.action == "add":
        name = " ".join(args.name).strip()
        if not name:
            return fail("usage: tasks add <name...>")
        task = store.add(name, clock.iso())
        store.save()
        return emit({"added": store.compact_view(task)})
    if args.action == "seed":
        added = []
        for name in config_module.SEED_TASKS:
            if store_module.task_id_for(name) not in store.tasks:
                added.append(store.compact_view(store.add(name, clock.iso())))
        store.save()
        return emit({"seeded": added})
    if args.action == "remove":
        try:
            task = store.get(args.task)
        except KeyError as error:
            return fail(str(error))
        store.remove(task.id)
        store.save()
        return emit({"removed": store.compact_view(task)})
    return fail("unknown action", 1)


def cmd_done(args: argparse.Namespace) -> int:
    store = MotherStore(home())
    try:
        task = store.get(args.task)
    except KeyError as error:
        return fail(str(error))
    note = " ".join(args.note).strip() or None
    store.set_status(task, today_iso(store.home), Status.DONE, note)
    return emit({"recorded": store.compact_view(task), "status": str(Status.DONE), "note": note})


def cmd_skip(args: argparse.Namespace) -> int:
    store = MotherStore(home())
    try:
        task = store.get(args.task)
    except KeyError as error:
        return fail(str(error))
    motivo = " ".join(args.motivo).strip()
    store.set_status(task, today_iso(store.home), Status.SKIPPED, motivo or None)
    return emit({"recorded": store.compact_view(task), "status": str(Status.SKIPPED), "motivo": motivo})


def cmd_checkup(args: argparse.Namespace) -> int:
    store = MotherStore(home())
    cfg = config_module.load(store.home)
    charged: list[str] = []
    if args.mark_missed and cfg.get("checkup_enabled", True):
        charged = checkup_module.mark_missed(store.all(), clock.now(cfg["timezone"]).date())
        if charged:
            store.save()
    report = checkup_module.build(store.all(), clock.now(cfg["timezone"]).date(), cfg["proof_after"])
    report["charged"] = charged
    return emit(report)


def cmd_recap(args: argparse.Namespace) -> int:
    store = MotherStore(home())
    cfg = config_module.load(store.home)
    report = recap_module.weekly(store.all(), clock.now(cfg["timezone"]).date(), args.days)
    return emit(report)


def cmd_config(args: argparse.Namespace) -> int:
    store_home = home()
    if args.action == "get":
        cfg = config_module.load(store_home)
        return emit(cfg if not args.key else {args.key: cfg.get(args.key)})
    if args.action == "set":
        if not args.key or args.value is None:
            return fail("usage: config set <key> <value>")
        cfg = config_module.load(store_home)
        raw = args.value
        parsed: object = raw
        if raw.lower() in ("true", "false"):
            parsed = raw.lower() == "true"
        elif raw.lstrip("-").isdigit():
            parsed = int(raw)
        cfg[args.key] = parsed
        config_module.save(store_home, cfg)
        return emit({"set": {args.key: parsed}})
    return fail("unknown action", 1)


def main() -> int:
    parser = argparse.ArgumentParser(prog="mother.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    tasks = sub.add_parser("tasks")
    tasks_sub = tasks.add_subparsers(dest="action", required=True)
    tasks_sub.add_parser("list")
    add = tasks_sub.add_parser("add")
    add.add_argument("name", nargs="+")
    tasks_sub.add_parser("seed")
    remove = tasks_sub.add_parser("remove")
    remove.add_argument("task")

    done = sub.add_parser("done")
    done.add_argument("task")
    done.add_argument("--note", nargs="*", default=[])

    skip = sub.add_parser("skip")
    skip.add_argument("task")
    skip.add_argument("--motivo", nargs="*", default=[])

    checkup = sub.add_parser("checkup")
    checkup.add_argument("--mark-missed", action="store_true")

    recap = sub.add_parser("recap")
    recap.add_argument("--days", type=int, default=7)

    cfg = sub.add_parser("config")
    cfg_sub = cfg.add_subparsers(dest="action", required=True)
    cfg_get = cfg_sub.add_parser("get")
    cfg_get.add_argument("key", nargs="?")
    cfg_set = cfg_sub.add_parser("set")
    cfg_set.add_argument("key")
    cfg_set.add_argument("value")

    handlers = {"tasks": cmd_tasks, "done": cmd_done, "skip": cmd_skip,
                "checkup": cmd_checkup, "recap": cmd_recap, "config": cmd_config}
    args = parser.parse_args()
    try:
        return handlers[args.command](args)
    except KeyError as error:
        return fail(str(error))
    except Exception as error:  # a CLI crash must never read like a state error
        return emit({"error": f"{type(error).__name__}: {error}"}, 1)


if __name__ == "__main__":
    sys.exit(main())

"""The CLI speaks one JSON object per turn, with the day boundary from config."""

import importlib.util
import json
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "skills" / "mother-checkup" / "scripts"
_spec = importlib.util.spec_from_file_location("mother_cli", _SCRIPTS / "mother.py")
cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cli)


def run(monkeypatch, home, *argv, tz="America/Sao_Paulo"):
    monkeypatch.setenv("MOTHER_HOME", home)
    if tz:
        monkeypatch.setenv("TZ", tz)
    if tz:
        monkeypatch.setattr(cli.config_module, "load", lambda h: {**cli.config_module.DEFAULTS, "timezone": tz})
    monkeypatch.setattr("sys.argv", ["mother.py", *argv])
    return cli.main()


def last_line(capsys):
    """The last JSON object printed -- every run() emits exactly one."""
    out = capsys.readouterr().out
    decoder, objects, index = json.JSONDecoder(), [], 0
    while index < len(out):
        if not out[index].isspace():
            obj, index = decoder.raw_decode(out, index)
            objects.append(obj)
        else:
            index += 1
    return objects[-1]


def test_seed_then_done_then_checkup(monkeypatch, home, capsys):
    assert run(monkeypatch, home, "tasks", "seed") == 0
    assert len(last_line(capsys)["seeded"]) == 4
    assert run(monkeypatch, home, "done", "arrumar o quarto", "--note", "de manhã") == 0
    assert last_line(capsys)["status"] == "feito"
    assert run(monkeypatch, home, "checkup") == 0
    report = last_line(capsys)
    ids = {row["id"] for row in report["tasks"]}
    assert ids == {"lavar-louca", "jogar-o-lixo-fora", "arrumar-o-quarto", "treinar"}
    assert report["pending"] == ["lavar-louca", "jogar-o-lixo-fora", "treinar"]


def test_skip_records_motivo(monkeypatch, home, capsys):
    run(monkeypatch, home, "tasks", "add", "treinar")
    assert run(monkeypatch, home, "skip", "treinar", "--motivo", "dor no joelho") == 0
    assert last_line(capsys)["motivo"] == "dor no joelho"


def test_unknown_task_exits_2(monkeypatch, home, capsys):
    assert run(monkeypatch, home, "done", "nao-existe") == 2
    assert "error" in last_line(capsys)


def test_mark_missed_charges_silence(monkeypatch, home, capsys):
    run(monkeypatch, home, "tasks", "add", "treinar")
    assert run(monkeypatch, home, "checkup", "--mark-missed") == 0
    row = last_line(capsys)["tasks"][0]
    assert row["status"] == "falta" and row["answered"] is True


def test_config_roundtrip(monkeypatch, home, capsys):
    assert run(monkeypatch, home, "config", "set", "timezone", "America/Sao_Paulo") == 0
    assert run(monkeypatch, home, "config", "get", "timezone") == 0
    assert last_line(capsys)["timezone"] == "America/Sao_Paulo"


def test_day_boundary_comes_from_config_zone(monkeypatch, home, capsys):
    # 23:00 UTC is already the next day in São Paulo; the ledger must say so.
    import datetime
    from kit import clock
    fake = datetime.datetime(2026, 9, 13, 23, 0, tzinfo=datetime.timezone.utc)
    clock.use_clock(lambda: fake)
    try:
        run(monkeypatch, home, "tasks", "add", "treinar", tz=None)
        assert run(monkeypatch, home, "done", "treinar", tz=None) == 0
        run(monkeypatch, home, "config", "set", "timezone", "America/Sao_Paulo", tz=None)
        assert run(monkeypatch, home, "checkup", tz=None) == 0
        row = last_line(capsys)["tasks"][0]
        assert row["status"] == "feito" and row["answered"] is True
    finally:
        clock.use_clock(None)

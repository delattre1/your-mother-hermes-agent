"""The store: one task per slug, day entries overwriting, find by id or name."""

import pytest

from mother.models import Status, Task
from mother.store import MotherStore, task_id_for


def test_slug_normalizes(store):
    assert task_id_for("Arrumar o quarto") == task_id_for("arrumar o quarto") == "arrumar-o-quarto"


def test_add_is_idempotent_by_slug(store):
    first = store.add("Arrumar o quarto", "2026-09-13T12:00:00+00:00")
    again = store.add("arrumar o quarto", "2026-09-13T18:00:00+00:00")
    assert first.id == again.id and len(store.all()) == 1


def test_get_by_id_and_by_name(store):
    store.add("Treinar", "2026-09-13T12:00:00+00:00")
    assert store.get("treinar").name == "Treinar"
    assert store.get("Treinar").id == "treinar"
    with pytest.raises(KeyError):
        store.get("lavar louça")


def test_later_word_overwrites_same_day(store):
    task = store.add("treinar", "2026-09-13T12:00:00+00:00")
    store.set_status(task, "2026-09-13", Status.MISS)
    store.set_status(task, "2026-09-13", Status.DONE, "depois da cobrança")
    entry = task.entry_for("2026-09-13")
    assert entry["status"] == str(Status.DONE)
    assert entry["motivo"] == "depois da cobrança"


def test_store_roundtrip(store):
    task = store.add("jogar o lixo fora", "2026-09-13T12:00:00+00:00")
    task.set_entry("2026-09-12", Status.SKIPPED, "chuva")
    store.save()
    other = MotherStore(store.home)
    loaded_task = other.get("jogar-o-lixo-fora")
    assert loaded_task.history["2026-09-12"] == {"status": "pulou", "motivo": "chuva"}
    assert loaded_task.created_at == task.created_at

"""Pure engine: streaks, the checkup, the escalation to a photo, the recap."""

from datetime import date

from mother.engine import checkup, recap, streak
from mother.models import Status, Task


def task_with(history: dict[str, str]) -> Task:
    task = Task(id="t", name="t", created_at="2026-09-01T00:00:00+00:00")
    for day, status in history.items():
        task.set_entry(day, Status(status))
    return task


TODAY = date(2026, 9, 13)


class TestStreak:
    def test_streak_counts_back_from_today(self):
        task = task_with({"2026-09-13": "feito", "2026-09-12": "feito", "2026-09-11": "pulou"})
        assert streak.current_streak(task, TODAY) == 2

    def test_pending_today_does_not_break_yesterday_streak(self):
        task = task_with({"2026-09-12": "feito", "2026-09-11": "feito"})
        assert streak.current_streak(task, TODAY) == 2

    def test_gap_breaks_but_does_not_charge(self):
        task = task_with({"2026-09-13": "feito", "2026-09-11": "feito"})  # 12: no entry
        assert streak.current_streak(task, TODAY) == 1

    def test_misses_stop_at_first_answer(self):
        task = task_with({"2026-09-13": "falta", "2026-09-12": "falta", "2026-09-11": "pulou"})
        assert streak.consecutive_misses(task, TODAY) == 2

    def test_best_streak_inside_window(self):
        task = task_with({f"2026-09-{d:02d}": "feito" for d in range(1, 6)})
        task.set_entry("2026-09-03", Status.SKIPPED)
        assert streak.best_streak_between(task, date(2026, 9, 1), TODAY) == 2


class TestCheckup:
    def test_pending_and_all_done(self):
        a = Task(id="a", name="a", created_at="x")
        b = Task(id="b", name="b", created_at="x")
        b.set_entry(TODAY.isoformat(), Status.DONE)
        report = checkup.build([a, b], TODAY)
        assert report["pending"] == ["a"] and report["all_done"] is False
        assert report["tasks"][1]["answered"] is True

    def test_empty_list_is_not_all_done(self):
        report = checkup.build([], TODAY)
        assert report["no_tasks"] is True and report["all_done"] is False

    def test_today_miss_completes_the_escalation(self):
        task = task_with({"2026-09-12": "falta", "2026-09-11": "falta"})
        row = checkup.build([task], TODAY, proof_after=3)["tasks"][0]
        assert row["need_photo"] is True  # two misses on record + tonight's

    def test_answer_breaks_escalation(self):
        task = task_with({"2026-09-12": "falta", "2026-09-11": "falta"})
        task.set_entry(TODAY.isoformat(), Status.SKIPPED, "viagem")
        row = checkup.build([task], TODAY, proof_after=3)["tasks"][0]
        assert row["need_photo"] is False and row["status"] == "pulou"

    def test_one_miss_is_far_from_a_photo(self):
        row = checkup.build([Task(id="a", name="a", created_at="x")], TODAY, proof_after=3)["tasks"][0]
        assert row["need_photo"] is False

    def test_mark_missed_charges_only_silent_tasks(self):
        a = Task(id="a", name="a", created_at="x")
        b = Task(id="b", name="b", created_at="x")
        b.set_entry(TODAY.isoformat(), Status.DONE)
        charged = checkup.mark_missed([a, b], TODAY)
        assert charged == ["a"] and a.entry_for(TODAY.isoformat())["status"] == "falta"
        assert b.entry_for(TODAY.isoformat())["status"] == "feito"


class TestRecap:
    def test_week_counts_and_worst(self):
        t1 = Task(id="q", name="quarto", created_at="x")
        t2 = Task(id="t", name="treinar", created_at="x")
        for day in ("2026-09-07", "2026-09-08", "2026-09-09"):
            t1.set_entry(day, Status.DONE)
        t2.set_entry("2026-09-07", Status.MISS)
        t2.set_entry("2026-09-08", Status.SKIPPED, "viagem")
        t2.set_entry("2026-09-09", Status.MISS)
        report = recap.weekly([t1, t2], date(2026, 9, 13))
        by_id = {row["id"]: row for row in report["tasks"]}
        assert by_id["q"]["feito"] == 3 and by_id["q"]["best_streak"] == 3
        assert by_id["t"]["faltas"] == 2 and by_id["t"]["pulou"] == 1
        assert report["worst"]["id"] == "t"

    def test_clean_week_has_no_worst_but_rows(self):
        report = recap.weekly([Task(id="a", name="a", created_at="x")], date(2026, 9, 13))
        assert report["worst"] is None or report["worst"]["faltas"] == 0

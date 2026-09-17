"""One simulated user, one full week. The engine's behaviour as a story: a
chore is done, one is skipped with a motive, one goes silent long enough to
earn the photo, and the Sunday recap says which was worst.

Pure: dates are injected, no clock, no network. This is the battery that
proves the charge is a function of the ledger, not of what the model felt
like saying that turn."""

from datetime import date

from mother.engine import checkup, recap, streak
from mother.models import Status, Task


def make(*names: str) -> list[Task]:
    tasks = []
    for name in names:
        tasks.append(Task(id=name.replace(" ", "-"), name=name,
                          created_at="2026-09-01T00:00:00+00:00"))
    return tasks


def close_day(tasks: list[Task], day: date, overrides: dict[str, Status]) -> None:
    """The checkup charges silence, then the user's answers land."""
    checkup.mark_missed(tasks, day)
    for name, status in overrides.items():
        task = next(t for t in tasks if t.name == name)
        task.set_entry(day.isoformat(), status)


def sim_week() -> list[Task]:
    quarto, louca, lixo, treinar = make("arrumar o quarto", "lavar louça",
                                        "jogar o lixo fora", "treinar")
    tasks = [quarto, louca, lixo, treinar]
    week = [date(2026, 9, 7) + __import__("datetime").timedelta(days=i) for i in range(7)]

    # Mon: a clean day -- everything done.
    close_day(tasks, week[0], {t.name: Status.DONE for t in tasks})
    # Tue: one skip with a motive, the rest done.
    close_day(tasks, week[1], {t.name: Status.DONE for t in tasks}
              | {"treinar": Status.SKIPPED})
    # Wed..Sat: the room goes silent; the rest stay done.
    for day in week[2:6]:
        close_day(tasks, day, {t.name: Status.DONE for t in tasks}
                  | {"arrumar o quarto": None if False else Status.MISS})
    return tasks, week


def test_silent_room_escalates_to_photo_by_the_fourth_night():
    tasks, week = sim_week()
    # Wed night (week[2] closed as miss), Thu night (week[3] miss), Fri night
    # (week[4] miss): three consecutive misses on the room.
    fri = checkup.build(tasks, week[4], proof_after=3)
    room = next(r for r in fri["tasks"] if r["id"] == "arrumar-o-quarto")
    assert room["consecutive_misses"] == 3
    assert room["need_photo"] is True


def test_skip_with_motive_is_not_a_miss():
    tasks, week = sim_week()
    row = next(r for r in checkup.build(tasks, week[1], proof_after=3)["tasks"]
               if r["id"] == "treinar")
    assert row["status"] == "pulou"
    assert row["consecutive_misses"] == 0


def test_done_after_a_charge_overwrites_the_miss():
    tasks, week = sim_week()
    # Sat: the checkup ran first and charged the room a fourth time...
    checkup.mark_missed(tasks, week[5])
    room = next(t for t in tasks if t.name == "arrumar o quarto")
    assert room.entry_for(week[5].isoformat())["status"] == "falta"
    # ...then the user did it at 22:00. The record says the correction.
    room.set_entry(week[5].isoformat(), Status.DONE)
    row = next(r for r in checkup.build(tasks, week[5], proof_after=3)["tasks"]
               if r["id"] == "arrumar-o-quarto")
    assert row["status"] == "feito"


def test_cleanest_task_keeps_a_six_day_streak():
    tasks, week = sim_week()
    louca = next(t for t in tasks if t.name == "lavar louça")
    assert streak.current_streak(louca, week[5]) == 6


def test_recap_names_the_worst():
    tasks, week = sim_week()
    report = recap.weekly(tasks, week[6])
    assert report["worst"]["id"] == "arrumar-o-quarto"
    assert report["worst"]["faltas"] >= 3
    # The skip kept its motive on the record, not folded into faltas.
    treinar = next(r for r in report["tasks"] if r["id"] == "treinar")
    assert treinar["pulou"] == 1


def test_empty_week_reports_zero_not_chaos():
    tasks = make("lavar louça")
    report = recap.weekly(tasks, date(2026, 9, 13))
    assert report["no_tasks"] is False
    assert report["worst"] is None or report["worst"]["faltas"] == 0

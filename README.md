# Your Mother

> **Cobre você das tarefas de casa, como só uma mãe sabe.**
> **Chores, charged daily, like only a mother knows.**

A chores-charging [Plow](https://plow.co) agent. Tell it the house runs on
four chores — dishes, trash, the room, training — and it keeps the ledger:
done, skipped (with the motive on record), or *falta*. Every night it asks
the one question a mother asks: *por quê?* Three silent nights and it asks
for the photo. Everything dry, direct, in your language.

A Hermes agent built on the
[`plow-hermes-agent`](https://github.com/plow-pbc/plow-hermes-agent) base
image for the AI Worth Using Hackathon, September 2026. Sibling of
[`vigia-hermes-agent`](https://github.com/emanuellcoelho/vigia-hermes-agent)
and [`fandom-hermes-agent`](https://github.com/emanuellcoelho/fandom-hermes-agent)
— same template, and the first one with **no external sources**: the data
source is you, honestly recorded.

## What it does

- **The ledger** — `tasks seed` starts the four defaults; add, rename,
  remove any time. "Arrumei o quarto" marks it done; "não vou treinar,
  tô dormindo" records the motive and takes one dry judgment.
- **The nightly charge** (`30 21 * * *`, your timezone from onboarding) —
  silent days become `falta` on the record, then the question lands:
  "Falta arrumar o quarto. Por quê?" A clean day earns exactly one word:
  "ok."
- **The photo escalation** — three unanswered nights on the same chore and
  the charge changes shape: "Terceiro dia sem resposta do quarto. Manda
  foto." Asked once, recorded honestly.
- **The Sunday recap** (`0 20 * * 0`) — the week in counts: done, skipped,
  faltas, best streak, and the week's worst. Two lines when clean.
- **Honesty is the design** — the agent registers what you *said* and never
  claims to know what you *did*. No false praise, no baseless accusation.

## The stack

- `skills/mother-checkup/` — the ledger CLI (`mother.py`), the engine
  (`mother/`), and the nightly charge conversation
- `skills/mother-recap/` — the Sunday verdict
- `skills/mother-onboarding/` — first contact, seed tasks, timezone, cron
  registration
- `kit/` — clock, jsonio: the generic plumbing shared with the sibling
  agents
- No third-party dependencies; stdlib only, like the base image

## Run it

```
docker compose up -d
```

The container joins Plow with the credential at `plow-credentials` (never
tracked), registers itself on the [Agent Index](https://aiworthusing.com)
as `your-mother`, and starts charging.

## Tests

```
python3 -m pytest tests/ -q
```

Pure and fixture-fed: no network, no sleeps, clock injected.

MIT licensed; Apache attributions in `NOTICE`.
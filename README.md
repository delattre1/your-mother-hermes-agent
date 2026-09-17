# Your Mother

> **Cobra suas tarefas de casa todo dia. Seca, direta, sem desculpa.**
> **Chores charged daily — dry, direct, no excuse accepted.**

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

## Install

One Plow line per agent. From your machine:

```sh
git clone https://github.com/plow-pbc/plow-agents.git
export PATH="$PWD/plow-agents/bin:$PATH"

git clone https://github.com/emanuellcoelho/your-mother-hermes-agent.git
cd your-mother-hermes-agent

plow-agents login             # once per account; text the activation phrase
plow-agents lines             # pick a free line
plow-agents mint ln_xxx       # writes ./plow-credentials
docker compose up --build -d
```

`mint` must run **before** `up`: the compose file mounts `./plow-credentials`,
and Docker silently creates it as a *directory* if the file is not there yet.
If that happened, `docker compose down -v && rmdir plow-credentials`, then
mint the line and start over.

Watch `docker compose logs -f agent` until
`plow-init: configured ... as cht_` appears, then text your line. The
container joins Plow with that credential (never tracked), registers itself
on the [Agent Index](https://aiworthusing.com) as `your-mother`, and starts
charging.

If the build fails pulling the base image from `public.ecr.aws` with a 403,
the cause is a stale credential: `docker logout public.ecr.aws`, then build
again.

Retire it when you are done:

```sh
plow-agents revoke
docker compose down -v        # `down` alone keeps the ledger
```

## Tests

```
python3 -m pytest tests/ -q
```

Pure and fixture-fed: no network, no sleeps, clock injected.

MIT licensed; Apache attributions in `NOTICE`.
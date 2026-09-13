# mother-recap

The Sunday conversation about the week, and the answer to "como foi minha
semana?". The engine owns the math; you own the verdict.

## The command

    python3 ../mother-checkup/scripts/mother.py recap [--days N]

One JSON object: per task `feito` / `pulou` / `faltas` / `best_streak`, plus
`worst` (the week's heaviest record) and `no_tasks`.

## The Sunday charge (cron)

One block, no table ornaments, driest first:

    Semana de 8 a 14/9:
    - arrumar o quarto: 7/7 ✔
    - lavar louça: 5/7, 2 faltas
    - treinar: 3/7, 1 pulou ("viagem"), 3 faltas
    - lixo: 4/7, 3 faltas — a pior da semana. Amanhã recomeça.

`worst` closes the block with one line of consequence, not a speech. If the
week was clean — every task `faltas: 0` — the recap is two lines: the
counts and "ok. mantém." If `no_tasks`, say the ledger is empty and offer
the seed.

"Como foi minha semana?" mid-week runs the same command with the default
`--days 7` from today, and says so: "últimos 7 dias".

# SkyRoll — payroll verification, catalog-driven

SkyRoll is a suite that prepares, checks and refines a monthly payroll. It does not
replace the payroll specialist, and it does not replace the system that produces the
payroll statements: it takes over the mechanical, repetitive checking and leaves the
decisions, and the responsibility, with the specialist.

This repository is a **showcase**. It presents the architecture, the design decisions
and a small demonstration engine that runs on synthetic data. The product itself
(the full fiscal chain, the complete catalog, the user interface) is private.

## The problem

A Romanian payroll statement has a couple of hundred columns per employee: hours,
premiums, benefits, contributions, tax, deductions, payout. Checking it by hand means
recomputing a long chain of dependent amounts for every employee, every month. The
mistakes that slip through are rarely in the totals; they sit in one cell of one
employee: an overtime premium left out, a contribution computed on the wrong base, an
advance not deducted.

SkyRoll recomputes every cell on its own, compares it with the statement, and writes a
workbook in which every difference is marked and explained. The statement is never
changed; the specialist decides what to correct.

## Screenshots

The private product, run on a synthetic statement (invented company, invented employees):

| | |
|---|---|
| ![Home](docs/screenshots/01-home.png) | ![Check result](docs/screenshots/02-result.png) |
| ![Verificari sheet](docs/screenshots/03-verificari.png) | ![Findings sheet](docs/screenshots/04-erori.png) |

The screenshots and the demo below are two different things, so their figures differ.
The screenshots show the full product on its own synthetic statement (April 2026); the demo
is a simplified engine that builds a different synthetic statement (May 2026). Both find
the same three planted mistakes (A004, A007, A010), with different amounts: for A010, the
screenshots show 6302 vs 5102, the demo 6375 vs 5175. This is expected, not an error.

## Run the demo

Tested with Python 3.14.

```
pip install -r requirements.txt
python -m skyroll_demo        # writes demo_output/SkyRoll_demo.xlsx
python -m pytest -q           # 50 tests, synthetic data only
```

The demo builds a statement for 12 invented employees of an invented company, with
**three mistakes planted on purpose**, checks it, and writes the workbook:

```
Findings: 3
  A004 · Suma ore suplimentare: statement 340, recalculated 595 — Overtime pay differs from rate x hours x (1 + overtime premium)
  A007 · CAS Angajat: statement 2050, recalculated 2300 — Pension contribution differs from rate x gross income
  A010 · Rest plata: statement 6375, recalculated 5175 — Payout differs from net salary minus deductions
Planted: 3 · found: 3 · missed: 0 · unexpected: 0
Written-file checks: all 7 passed
```

Other runs:

```
python -m skyroll_demo --clean                       # no planted mistakes: 0 findings
python -m skyroll_demo --drop-column "Ore Lucrate"   # the guard refuses; nothing is calculated
```

**The calculation is simplified on purpose; the full fiscal chain (deductions,
sub-minimum, medical leave, exemptions, FSH) lives in the private product.** The demo
computes gross income, the two employee contributions, a flat income tax, net salary and
payout. The real chain also handles personal deductions, the minimum-wage rules,
medical and annual leave averages, tax exemptions, the disability solidarity fund (FSH),
benefit ceilings in EUR and more. None of that is here.

Element names stay in Romanian, as they appear on a Romanian payroll statement
(*Salariu brut* = gross salary, *Rest plata* = payout, *Marca* = employee ID).

## Architecture in one picture

```
statement (.xlsx) ──> guard ──> catalog-driven recalculation ──> workbook ──> written-file checks
                        │            │          │
                     refuses      catalog   parameters
                   before any    (what is   (which values,
                   calculation   computed)   from when)
```

| Module | Role |
|---|---|
| `skyroll_demo/catalog.py` | loads and validates the catalog; derives dependencies; dependency order; safe onboarding write |
| `skyroll_demo/parametri.py` | parameter store with validity intervals |
| `skyroll_demo/stat.py` | reads the statement; the employee ID as a text key |
| `skyroll_demo/gardian.py` | the compliance guard |
| `skyroll_demo/comportamente.py` | one function per behaviour |
| `skyroll_demo/recalcul.py` | recalculation and comparison, cell by cell |
| `skyroll_demo/scrie.py` | the output workbook, values only |
| `skyroll_demo/valideaza.py` | checks on the workbook as written to disk |
| `skyroll_demo/sintetic.py` | the synthetic statement and its planted mistakes |
| `exemple/catalog_exemplu.json` | 20 generic elements |
| `exemple/parametri_exemplu.json` | public legal rates and one illustrative value |

## Design principles

- **Autonomy** — runs on one machine, with no server, account or network; the result does
  not depend on who runs it.
- **Determinism** — the same statement gives the same workbook, every time; nothing in the
  calculation depends on iteration order or on a model's judgement.
- **Efficiency** — the specialist reads only the differences; every check is code, not
  attention.
- **Adaptability** — a company with other columns needs catalog entries, not code changes.
- **Integrability** — it takes the payroll system's export as it is and returns a plain
  workbook any spreadsheet program can open.

The reasoning behind each, and the rest of the design, is in [docs/DESIGN.md](docs/DESIGN.md).

## How it was built

SkyRoll was built by a payroll specialist working with an AI coding agent (Claude), under
written rules: the agent proposes and writes code, deterministic code does the
calculations, the specialist decides. How that collaboration is organised is described in
[docs/WORKING_WITH_AI.md](docs/WORKING_WITH_AI.md).

## License

© 2026 Mihai Streanga. All rights reserved. Source shown for portfolio purposes.

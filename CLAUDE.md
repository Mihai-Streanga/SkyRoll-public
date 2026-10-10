# SkyRoll showcase — instructions for Claude Code

This repository is the **showcase** of SkyRoll, a monthly payroll verification tool: the
architecture, the design decisions and a demonstration engine (`skyroll_demo`) on synthetic
data. The product itself is private and is not here. Code, comments and docs are in English.
The reasons behind the rules below are in [docs/DESIGN.md](docs/DESIGN.md).

## Map

| file | what it holds |
|---|---|
| `skyroll_demo/catalog.py` | the catalog: the single description of what a statement contains, and the calculation order |
| `skyroll_demo/gardian.py` | the compliance guard: refuses a statement before anything is calculated |
| `skyroll_demo/recalcul.py`, `comportamente.py` | independent recalculation of every computed cell |
| `skyroll_demo/parametri.py` | the parameters the law or the employer sets, each with a validity interval |
| `skyroll_demo/stat.py` | reading a statement |
| `skyroll_demo/scrie.py`, `valideaza.py` | writing the workbook and checking it as written to disk |
| `skyroll_demo/sintetic.py` | the synthetic statement: 12 invented employees of an invented company |
| `exemple/` | the example catalog and parameters |

## Commands

```bat
python -m pip install -r requirements.txt
python -m pytest -q
python -m skyroll_demo
python -m skyroll_demo --clean
python -m skyroll_demo --drop-column "Ore Lucrate"
```

## Rules

- **Synthetic data only.** No real statement, person, employer or payroll register ever enters
  this repository, not even as a test fixture.
- **The guard comes first.** A statement that fails the guard raises `StatementRefused` and
  nothing is calculated on it. Do not weaken the guard to let a run through.
- **Deterministic.** The calculation order is a topological sort of the dependencies, ties broken
  alphabetically (`topological_order` in `catalog.py`). Rounding is explicit half-up with
  `Decimal`, as payroll does, never Python's `round()`.
- **The catalog is the single description.** A new column becomes a catalog entry; the engine
  does not change. Dependencies are derived, not maintained by hand.
- **Columns are read by name**, never by position.
- **The output is values only**, no formulas, readable in any spreadsheet program; what was
  written is checked on the file on disk, not on what the program believes it wrote.
- **The statement is never changed.** Every difference is marked and explained; the specialist
  decides what to correct.

# SkyRoll — design

This document explains how SkyRoll is built and why. The demonstration engine in this
repository follows the same design on a reduced scale; where the private product does
more, the text says so.

## 1. Scope and non-goals

SkyRoll **checks** a payroll statement; it does not **produce** one. The statement comes
from the company's payroll system; SkyRoll rebuilds every amount independently, compares,
and reports. It never corrects the statement, never decides, and never presents a number
it could not justify from the statement and the parameters.

Non-goals: replacing the payroll system; replacing the specialist's judgement; using a
language model to compute or to decide anything about the numbers.

## 2. Principles

**Autonomy.** The tool runs on the specialist's machine, with no server, no account and
no network access. Everything it needs is in the repository (code, catalog, parameters)
or is given to it (the statement). The result does not depend on who runs it: two
operators with the same statement get the same workbook.

**Determinism.** The same input produces the same output. The calculation order is a topological sort of the dependencies with
alphabetical tie-breaking, because iterating a set gives a different order from one
process to the next. Rounding is explicit half-up, as payroll does, not Python's default
half-to-even. In the private product, a hash of the produced workbook is the
non-regression check: any change to the engine must leave it identical, or explain why
not.

**Efficiency.** The specialist's attention is the scarce resource. The workbook shows the
differences, each one with the rule that was broken; a clean statement shows nothing. The
catalog is read once per run and the dependencies are derived, not maintained by hand.

**Adaptability.** Companies use different columns. A new column becomes a new catalog
entry; the engine does not change. The deduction columns are not listed anywhere: they
are whatever stands between net salary and payout in the statement.

**Integrability.** The input is the payroll system's export as it comes, read by column
name and not by position. The output is a plain workbook, values only, which opens in any
spreadsheet program and can be archived next to the statement it checks.

## 3. Catalog and parameters

Two files describe everything the engine knows, and they answer different questions.

The **catalog** says *what* is calculated. Each element (a column of the statement) has a
name and a behaviour; the behaviour's arguments name the elements it uses:

```json
{"nume": "CAS Angajat", "comportament": "cota", "fundamental": true,
 "argumente": {"baza_formula": [{"element": "Venit brut realizat", "semn": "+"}],
               "cota_param": "Cota CAS angajat", "rotunjire": 0},
 "toleranta": 1, "mesaj": "Pension contribution differs from rate x gross income"}
```

The behaviours form a closed set (identity key, operand, input, pay for hours, vouchers,
sum of components, signed formula, rate on a base, payout). An element can declare itself
a component of a sum (`intra_in`), so adding a new benefit to gross income is one entry,
with no list to update elsewhere. The demo catalog has 20 generic elements; the private
one has several hundred and more behaviours, including dedicated mechanisms for the parts
of the law that are not linear sums.

The **parameters** say *with which values, from when*: rates, ceilings, the minimum wage,
each with a start date and an optional end date. A change in the law is a new entry; a
statement from an earlier month is still checked with the values valid at the time.

Keeping the two apart means the law changes in one file and the shape of a company's
statement in the other, and neither change touches the code.

## 4. Onboarding a new column

A statement with a column the catalog does not know is not rejected: the column is
reported. In the product, the specialist then describes it in the interface (is it an
amount or a quantity? does it enter gross income? is it taxed?), and the answers become a
catalog entry. The entry is validated against the whole catalog in memory (known
behaviour, complete arguments, existing references, no dependency cycle) and only then
written, through a temporary file and an atomic replace, so the catalog on disk is never
half-written or invalid. The next run uses it. No code is written.

The demo includes the safe write (`catalog.add_element`) and its tests; the interface is
not part of it.

## 5. The compliance guard

A check that runs on an incomplete statement still produces numbers, and numbers look
like an answer. The guard runs first and refuses, with the exact reason, when:

- a required column is missing, or a column is present without the operands it needs;
- a column name appears twice;
- an employee ID is empty or used twice;
- an amount is not a number;
- the payout column stands before net salary (the deductions could not be located).

A refused statement produces no workbook. "No findings" can therefore only mean "checked
and clean", never "could not check". The private product's guard also identifies the
attached reports (employee data, history, medical leave) by their content rather than by
their file name, and stops when one is attached in the wrong place.

The employee ID is a text key everywhere. IDs such as "0042" or "B17" are not
numbers: converting them loses leading zeros and letters, and sorting them numerically
reorders them.

## 6. Independent recalculation

Every computed cell is rebuilt from its operands and compared with the statement, within
the tolerance declared for that element (0 for amounts the law defines exactly, 1 leu
where the payroll system's own rounding may legitimately differ). Each difference carries
the catalog's message, which says what the element should equal.

In the demo, each cell is recomputed from the statement's own values of its operands.
One mistake therefore produces one finding, at the cell where it was made, instead of a
cascade through every element downstream of it: an overtime amount paid without the
premium is reported on the overtime cell, not again on gross income, contributions, tax,
net salary and payout.

## 7. Checking what was written

After the workbook is written, it is read back from disk and checked; the program does
not trust its own memory of what it wrote. This showcase's own list of checks:

1. **sheets** — the three sheets exist, in order, and nothing else;
2. **values** — no cell holds a formula;
3. **copy** — the statement sheet is the statement, cell for cell;
4. **mirror** — every statement value in the comparison sheet equals the copied cell;
5. **tolerance** — a recalculated cell is marked exactly when it is outside tolerance;
6. **findings** — the marked cells and the findings list are the same set;
7. **payout** — the recalculated payout equals net salary minus the deductions,
   re-derived from the written copy.

If any check fails, the run ends with a non-zero exit code. The private product applies
a longer list of the same kind and does not hand over a workbook that fails it.

## 8. Data security

Payroll statements contain names, personal identification numbers, bank accounts and
salaries. The design keeps them away from everything that could leak them:

- **Real data never enters a repository.** Statements live in one local folder that
  version control ignores, together with every spreadsheet and document format
  (`.xls`, `.xlsx`, `.xlsm`, `.xlsb`, `.csv`, `.ods`, `.pdf`), wherever such a file
  might land.
- **The AI agent cannot read that folder.** Its permissions deny it; tests that need real
  statements read them at run time and are skipped when the folder is absent.
- **What enters version control is code, catalog, parameters, hashes, counts and
  synthetic data.** Every test in this repository runs on invented data.
- **History is checked before anything is published.** The private repository's history
  was scanned for personal identification numbers, bank accounts, company identifiers,
  e-mail addresses and secrets (with gitleaks) before this showcase was derived from it.
  This showcase was written fresh, not copied from that history.

## 9. What is not in this repository

- the full fiscal chain and its dedicated mechanisms;
- medical leave and annual leave calculations;
- the complete catalog and the live parameter store;
- the reading of real payroll exports and their attached reports;
- the user interface, the operator manual and the technical specification;
- the private test suite and its reference data.

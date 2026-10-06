"""python -m skyroll_demo — generate a synthetic statement, check it, write the workbook.

Exit codes: 0 checked (findings or not), 2 statement refused by the guard,
3 the written workbook failed its own checks.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date

from . import CATALOG, PARAMETERS, SIMPLIFIED, catalog, gardian, recalcul, scrie, sintetic, stat, valideaza
from .parametri import Store


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m skyroll_demo", description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="demo_output", help="output folder (default: demo_output)")
    ap.add_argument("--clean", action="store_true", help="synthetic statement without the planted mistakes")
    ap.add_argument("--drop-column", metavar="NAME", help="remove a column, to see the guard refuse")
    ap.add_argument("--statement", metavar="XLSX", help="check this statement instead of a synthetic one")
    ap.add_argument("--month", default=sintetic.MONTH.strftime("%Y-%m"), help="YYYY-MM (default 2026-05)")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    cat = catalog.load(CATALOG)
    params = Store.load(PARAMETERS)
    month = date.fromisoformat(a.month + "-01")
    os.makedirs(a.out, exist_ok=True)

    planted = []
    if a.statement:
        path = a.statement
    else:
        headers, rows = sintetic.build(params, with_mistakes=not a.clean)
        planted = [] if a.clean else sintetic.PLANTED
        if a.drop_column:
            headers = [h for h in headers if h != a.drop_column]
        path = sintetic.write(os.path.join(a.out, "stat_sintetic.xlsx"), headers, rows)
    statement = stat.read(path)
    print(f"SkyRoll demo — {sintetic.COMPANY if not a.statement else os.path.basename(path)}, "
          f"{month:%Y-%m}{' (synthetic data)' if not a.statement else ''}")
    print(f"Statement: {path} ({len(statement.rows)} employees, {len(statement.headers)} columns)")

    try:
        result = recalcul.run(statement, cat, params, month)
    except gardian.StatementRefused as e:
        print("Guard: REFUSED — nothing was calculated")
        for p in e.report.problems:
            print(f"  - {p}")
        return 2

    unknown = ", ".join(result.unknown_columns) or "none"
    print(f"Guard: compliant · columns not in the catalog: {unknown}")
    print(f"Checked: {len(statement.rows)} employees x {len(result.elements)} elements "
          f"= {len(result.checks)} cells, in dependency order")
    print(f"Findings: {len(result.findings)}")
    for c in result.findings:
        print(f"  {c.marca} · {c.element}: statement {scrie._num(c.in_statement)}, "
              f"recalculated {scrie._num(c.recalculated)} — {c.message}")

    if planted:
        want = {(p.marca, p.element) for p in planted}
        got = {(c.marca, c.element) for c in result.findings}
        print(f"Planted: {len(want)} · found: {len(want & got)} · missed: {len(want - got)} "
              f"· unexpected: {len(got - want)}")

    out = scrie.write(result, os.path.join(a.out, "SkyRoll_demo.xlsx"))
    ok, problems = valideaza.validate(out, statement, cat)
    print(f"Written-file checks: {'all 7 passed' if ok else 'FAILED'}")
    for p in problems:
        print(f"  - {p}")
    print(f"Workbook: {out}")
    print(f"Note: {SIMPLIFIED}.")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())

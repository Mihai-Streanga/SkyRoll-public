"""The compliance guard: refuse a statement before calculating anything on it.

A check that runs on an incomplete statement still produces numbers, and numbers look
like an answer. The guard stops first and says exactly what is missing, so "no
findings" can only ever mean "checked and clean", never "could not check".
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .catalog import COMPUTED, ELEMENT_ARGS, TERM_ARGS, Catalog
from .stat import Statement, marca_key, number


class StatementRefused(ValueError):
    def __init__(self, report: "Report"):
        super().__init__("; ".join(report.problems))
        self.report = report


@dataclass
class Report:
    problems: list[str] = field(default_factory=list)       # blocking
    unknown_columns: list[str] = field(default_factory=list)  # not blocking: candidates for onboarding

    @property
    def compliant(self) -> bool:
        return not self.problems


def _operands(name: str, e: dict) -> list[str]:
    args = e["argumente"]
    refs = [args[a] for a in ELEMENT_ARGS.get(e["comportament"], ())]
    key = TERM_ARGS.get(e["comportament"])
    if key:
        refs += [t["element"] for t in args[key]]
    return refs


def check(statement: Statement, catalog: Catalog) -> Report:
    r = Report()
    headers = statement.headers
    present = set(headers)

    dup = sorted(h for h, c in Counter(headers).items() if c > 1 and h)
    if dup:
        r.problems.append(f"duplicate columns: {dup}")
    missing = [n for n in catalog.fundamental() if n not in present]
    if missing:
        r.problems.append(f"missing required columns: {missing}")

    for name, e in catalog.elements.items():
        if name not in present or e["comportament"] not in COMPUTED:
            continue
        lacking = [o for o in _operands(name, e) if o not in present]
        if lacking:
            r.problems.append(f"'{name}' is in the statement but its operands are not: {lacking}")
        if e["comportament"] == "rest_plata":
            net = e["argumente"]["net"]
            if net in present and headers.index(net) > headers.index(name):
                r.problems.append(f"'{net}' must stand before '{name}' (deductions lie between them)")

    keys = [marca_key(v) for v in statement.column("Marca")] if "Marca" in present else []
    empty = [i + 2 for i, k in enumerate(keys) if not k]
    if empty:
        r.problems.append(f"rows without employee ID (Marca): {empty}")
    twice = sorted(k for k, c in Counter(keys).items() if c > 1 and k)
    if twice:
        r.problems.append(f"employee IDs used more than once: {twice}")

    numeric = [n for n, e in catalog.elements.items()
               if n in present and e["comportament"] not in ("cheie",)]
    for i, row in enumerate(statement.rows):
        for n in numeric:
            try:
                number(row.get(n))
            except (TypeError, ValueError):
                r.problems.append(f"row {i + 2}, '{n}': not a number ({row.get(n)!r})")

    r.unknown_columns = [h for h in headers if h and h not in catalog.elements]
    return r


def require(statement: Statement, catalog: Catalog) -> Report:
    report = check(statement, catalog)
    if not report.compliant:
        raise StatementRefused(report)
    return report

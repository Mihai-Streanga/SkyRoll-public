"""Independent recalculation: every computed cell of the statement, rebuilt and compared.

The statement is never corrected. Each difference larger than the element's tolerance
becomes a finding, with the catalog's message saying what the element should equal;
the decision about the correction stays with the payroll specialist.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from . import gardian
from .catalog import Catalog
from .comportamente import RECALC, Context
from .parametri import Store
from .stat import Statement, marca_key, number


@dataclass(frozen=True)
class Check:
    marca: str
    element: str
    in_statement: Decimal
    recalculated: Decimal
    tolerance: Decimal
    message: str

    @property
    def difference(self) -> Decimal:
        return self.in_statement - self.recalculated

    @property
    def is_finding(self) -> bool:
        return abs(self.difference) > self.tolerance


@dataclass
class Result:
    statement: Statement
    elements: list[str]              # checked elements, in dependency order
    checks: list[Check]
    unknown_columns: list[str]

    @property
    def findings(self) -> list[Check]:
        return [c for c in self.checks if c.is_finding]


def run(statement: Statement, catalog: Catalog, params: Store, month: date) -> Result:
    report = gardian.require(statement, catalog)          # refuses before any calculation
    present = set(statement.headers)
    elements = [n for n in catalog.computed() if n in present]
    ctx = Context(catalog, params, month, statement.headers)
    checks = []
    for row in statement.rows:
        for name in elements:
            e = catalog.elements[name]
            checks.append(Check(
                marca=marca_key(row.get("Marca")),
                element=name,
                in_statement=Decimal(str(number(row.get(name)))),
                recalculated=RECALC[e["comportament"]](name, e, row, ctx),
                tolerance=Decimal(str(e["toleranta"])),
                message=e["mesaj"],
            ))
    return Result(statement, elements, checks, report.unknown_columns)

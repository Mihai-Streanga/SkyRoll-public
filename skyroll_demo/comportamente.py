"""How each behaviour recalculates an element, for one employee.

Every operand is read from the statement itself (`row`), not from another
recalculated value. Each cell is therefore checked against its own inputs: one
mistake in the statement produces one finding, where the mistake was made, instead
of a cascade through every element downstream of it.
"""
from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable

from .catalog import Catalog
from .parametri import Store
from .stat import number


def rounded(value: Decimal, decimals: int | None) -> Decimal:
    """Half-up rounding, as payroll does (Python's round() rounds half to even)."""
    if decimals is None:
        return value
    return value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def _dec(x) -> Decimal:
    return Decimal(str(number(x)))


class Context:
    """What a behaviour may look at: the employee's row, the catalog, the parameters, the month."""

    def __init__(self, catalog: Catalog, params: Store, month: date, headers: list[str]):
        self.catalog, self.params, self.month, self.headers = catalog, params, month, headers

    def param(self, name: str) -> Decimal:
        return Decimal(str(self.params.value(name, self.month)))

    def deductions(self, net: str, payout: str) -> list[str]:
        """The deduction columns: strictly between net salary and payout, in the statement.

        Derived from where the columns stand, not from a fixed list, so a statement with
        a different set of deductions needs no change.
        """
        h = self.headers
        return h[h.index(net) + 1: h.index(payout)]


def _signed_sum(terms: list[dict], row: dict) -> Decimal:
    total = Decimal(0)
    for t in terms:
        v = _dec(row.get(t["element"]))
        total += v if t["semn"] == "+" else -v
    return total


def suma_pontaj(name, e, row, ctx: Context) -> Decimal:
    a = e["argumente"]
    norm = _dec(row.get(a["norma"]))
    if norm == 0:
        return Decimal(0)
    premium = Decimal(str(a["spor_implicit"]))
    if a["spor_param"]:
        premium = ctx.param(a["spor_param"])
    rate = _dec(row.get(a["salariu"])) / norm
    return rounded(rate * _dec(row.get(a["operand"])) * (1 + premium), a["rotunjire"])


def tichete(name, e, row, ctx: Context) -> Decimal:
    a = e["argumente"]
    return rounded(_dec(row.get(a["nr"])) * ctx.param(a["valoare_param"]), a["rotunjire"])


def suma_componente(name, e, row, ctx: Context) -> Decimal:
    parts = [c for c in ctx.catalog.components_of(name) if c in row]
    return rounded(sum((_dec(row.get(c)) for c in parts), Decimal(0)), e["argumente"]["rotunjire"])


def formula(name, e, row, ctx: Context) -> Decimal:
    a = e["argumente"]
    return rounded(_signed_sum(a["formula"], row), a["rotunjire"])


def cota(name, e, row, ctx: Context) -> Decimal:
    a = e["argumente"]
    return rounded(_signed_sum(a["baza_formula"], row) * ctx.param(a["cota_param"]), a["rotunjire"])


def rest_plata(name, e, row, ctx: Context) -> Decimal:
    a = e["argumente"]
    deducted = sum((_dec(row.get(d)) for d in ctx.deductions(a["net"], name)), Decimal(0))
    return rounded(_dec(row.get(a["net"])) - deducted, a["rotunjire"])


RECALC: dict[str, Callable[..., Decimal]] = {
    "suma_pontaj": suma_pontaj,
    "tichete": tichete,
    "suma_componente": suma_componente,
    "formula": formula,
    "cota": cota,
    "rest_plata": rest_plata,
}

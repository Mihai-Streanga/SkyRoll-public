"""A synthetic payroll statement: 12 invented employees of an invented company.

No value comes from a real statement. Every cell is computed the way a payroll system
would compute it, except for three mistakes planted on purpose, at known places, so
the demo can show that the check finds exactly those three and nothing else.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from openpyxl import Workbook

from .parametri import Store

COMPANY = "Firma Demo"
MONTH = date(2026, 5, 1)
NORM = 160

HEADERS = [
    "Marca", "Nume", "Prenume", "Salariu brut lei", "Ore lucratoare in luna", "Ore Lucrate",
    "Suma Ore Lucrate", "Ore suplimentare", "Suma ore suplimentare", "Bonus",
    "Venit brut realizat", "Nr Tichete masa", "Tichete de masa", "CAS Angajat", "CASS Angajat",
    "Venit net", "Impozit", "Salariu net", "Avans", "Rest plata",
]

# marca, gross salary, hours worked, overtime hours, bonus, advance
EMPLOYEES = [
    ("A001", 4500, 160, 0, 0, 0),
    ("A002", 5200, 160, 4, 0, 1000),
    ("A003", 6000, 152, 0, 300, 0),
    ("A004", 6800, 160, 8, 0, 0),
    ("A005", 7500, 144, 0, 0, 1500),
    ("A006", 4800, 160, 6, 250, 0),
    ("A007", 8200, 160, 0, 1000, 0),
    ("A008", 9000, 160, 10, 0, 2000),
    ("A009", 5600, 136, 0, 0, 0),
    ("A010", 10500, 160, 0, 500, 1200),
    ("A011", 12000, 160, 0, 0, 0),
    ("A012", 4300, 160, 2, 0, 500),
]


@dataclass(frozen=True)
class Planted:
    marca: str
    element: str
    what: str


PLANTED = [
    Planted("A004", "Suma ore suplimentare", "overtime paid without the overtime premium"),
    Planted("A007", "CAS Angajat", "pension contribution computed on gross income without the bonus"),
    Planted("A010", "Rest plata", "advance not deducted from the payout"),
]


def _r(x: Decimal) -> int:
    return int(x.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def build(params: Store, with_mistakes: bool = True) -> tuple[list[str], list[dict]]:
    p = {n: Decimal(str(params.value(n, MONTH))) for n in
         ("Cota CAS angajat", "Cota CASS angajat", "Cota impozit venit",
          "Spor ore suplimentare", "Valoare tichet masa")}
    mistakes = {(m.marca, m.element) for m in PLANTED} if with_mistakes else set()
    rows = []
    for i, (marca, salary, hours, overtime, bonus, advance) in enumerate(EMPLOYEES, start=1):
        rate = Decimal(salary) / NORM
        pay = _r(rate * hours)
        premium = 0 if (marca, "Suma ore suplimentare") in mistakes else p["Spor ore suplimentare"]
        ot_pay = _r(rate * overtime * (1 + premium))
        gross = pay + ot_pay + bonus
        vouchers_n = hours // 8
        vouchers = _r(vouchers_n * p["Valoare tichet masa"])
        cas_base = gross - bonus if (marca, "CAS Angajat") in mistakes else gross
        cas = _r(cas_base * p["Cota CAS angajat"])
        cass = _r(gross * p["Cota CASS angajat"])
        net_income = gross - cas - cass
        tax = _r((net_income + vouchers) * p["Cota impozit venit"])
        net = net_income - tax
        payout = net if (marca, "Rest plata") in mistakes else net - advance
        rows.append(dict(zip(HEADERS, [
            marca, "Angajat", f"{i:03d}", salary, NORM, hours, pay, overtime, ot_pay, bonus,
            gross, vouchers_n, vouchers, cas, cass, net_income, tax, net, advance, payout,
        ])))
    return list(HEADERS), rows


def write(path: str, headers: list[str], rows: list[dict], total_row: bool = True) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = "Stat"
    ws.append(headers)
    for r in rows:
        ws.append([r.get(h) for h in headers])
    if total_row:
        totals = [sum(r[h] for r in rows) if isinstance(rows[0].get(h), (int, float)) else None
                  for h in headers]
        totals[0] = f"Total {COMPANY}"
        ws.append(totals)
    wb.save(path)
    return path

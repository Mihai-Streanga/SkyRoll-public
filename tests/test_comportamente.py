from datetime import date
from decimal import Decimal

import pytest

from skyroll_demo.comportamente import RECALC, Context, rounded
from skyroll_demo.parametri import ParameterError

MONTH = date(2026, 5, 1)


def calc(cat, params, name, row, headers=None):
    e = cat.elements[name]
    ctx = Context(cat, params, MONTH, headers or list(row))
    return RECALC[e["comportament"]](name, e, row, ctx)


def test_rounding_is_half_up():
    assert rounded(Decimal("2.5"), 0) == 3
    assert rounded(Decimal("3.5"), 0) == 4
    assert rounded(Decimal("-2.5"), 0) == -3
    assert rounded(Decimal("1.005"), 2) == Decimal("1.01")
    assert rounded(Decimal("7.25"), None) == Decimal("7.25")


def test_pay_for_hours_worked(cat, params):
    row = {"Salariu brut lei": 6000, "Ore lucratoare in luna": 160, "Ore Lucrate": 152}
    assert calc(cat, params, "Suma Ore Lucrate", row) == 5700


def test_overtime_uses_the_premium_parameter(cat, params):
    row = {"Salariu brut lei": 6800, "Ore lucratoare in luna": 160, "Ore suplimentare": 8}
    assert calc(cat, params, "Suma ore suplimentare", row) == 595        # 42.5 x 8 x 1.75


def test_zero_norm_gives_zero_not_an_error(cat, params):
    row = {"Salariu brut lei": 6000, "Ore lucratoare in luna": 0, "Ore Lucrate": 10}
    assert calc(cat, params, "Suma Ore Lucrate", row) == 0


def test_meal_vouchers(cat, params):
    assert calc(cat, params, "Tichete de masa", {"Nr Tichete masa": 19}) == 570


def test_gross_income_sums_the_declared_components(cat, params):
    row = {"Suma Ore Lucrate": 6800, "Suma ore suplimentare": 595, "Bonus": 100}
    assert calc(cat, params, "Venit brut realizat", row) == 7495


def test_a_missing_optional_component_counts_as_absent(cat, params):
    assert calc(cat, params, "Venit brut realizat", {"Suma Ore Lucrate": 4000}) == 4000


def test_contribution_rate(cat, params):
    assert calc(cat, params, "CAS Angajat", {"Venit brut realizat": 9200}) == 2300
    assert calc(cat, params, "CASS Angajat", {"Venit brut realizat": 9201}) == 920


def test_signed_formula(cat, params):
    row = {"Venit brut realizat": 1000, "CAS Angajat": 250, "CASS Angajat": 100}
    assert calc(cat, params, "Venit net", row) == 650


def test_payout_deducts_every_column_between_net_and_payout(cat, params):
    headers = ["Marca", "Salariu net", "Avans", "Poprire", "Rest plata"]
    row = {"Salariu net": 5000, "Avans": 1000, "Poprire": 300, "Rest plata": 3700}
    assert calc(cat, params, "Rest plata", row, headers) == 3700


def test_a_column_after_payout_is_not_a_deduction(cat, params):
    headers = ["Marca", "Salariu net", "Avans", "Rest plata", "Observatii"]
    row = {"Salariu net": 5000, "Avans": 1000, "Observatii": 99}
    assert calc(cat, params, "Rest plata", row, headers) == 4000


def test_parameter_follows_the_month(params):
    assert params.value("Valoare tichet masa", date(2026, 5, 1)) == 30
    with pytest.raises(ParameterError, match="no value"):
        params.value("Valoare tichet masa", date(2025, 12, 1))

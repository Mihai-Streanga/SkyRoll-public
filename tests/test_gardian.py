import pytest

from skyroll_demo import gardian, recalcul
from skyroll_demo.stat import Statement, marca_key


def drop(statement, column):
    return Statement([h for h in statement.headers if h != column],
                     [{k: v for k, v in r.items() if k != column} for r in statement.rows])


def test_synthetic_statement_is_compliant(statement, cat):
    assert gardian.check(statement, cat).compliant


def test_missing_required_column_refuses(statement, cat):
    r = gardian.check(drop(statement, "Rest plata"), cat)
    assert not r.compliant
    assert "missing required columns: ['Rest plata']" in r.problems


def test_missing_optional_pair_is_accepted(statement, cat):
    s = drop(drop(statement, "Ore suplimentare"), "Suma ore suplimentare")
    assert gardian.check(s, cat).compliant


def test_element_without_its_operand_refuses(statement, cat):
    r = gardian.check(drop(statement, "Nr Tichete masa"), cat)
    assert any("'Tichete de masa' is in the statement but its operands are not" in p for p in r.problems)


def test_duplicate_employee_id_refuses(statement, cat):
    statement.rows[1]["Marca"] = statement.rows[0]["Marca"]
    assert any("more than once" in p for p in gardian.check(statement, cat).problems)


def test_empty_employee_id_refuses(statement, cat):
    statement.rows[3]["Marca"] = None
    assert "rows without employee ID (Marca): [5]" in gardian.check(statement, cat).problems


def test_text_in_an_amount_refuses(statement, cat):
    statement.rows[0]["Bonus"] = "n/a"
    assert any("'Bonus': not a number" in p for p in gardian.check(statement, cat).problems)


def test_unknown_column_is_reported_not_refused(statement, cat):
    s = Statement(statement.headers + ["Prima vacanta"], statement.rows)
    r = gardian.check(s, cat)
    assert r.compliant and r.unknown_columns == ["Prima vacanta"]


def test_refused_statement_is_never_calculated(statement, cat, params):
    from datetime import date
    with pytest.raises(gardian.StatementRefused):
        recalcul.run(drop(statement, "Ore Lucrate"), cat, params, date(2026, 5, 1))


@pytest.mark.parametrize("raw, key", [("A001", "A001"), (" A001 ", "A001"), (19.0, "19"),
                                      ("0042", "0042"), (None, "")])
def test_employee_id_stays_text(raw, key):
    assert marca_key(raw) == key

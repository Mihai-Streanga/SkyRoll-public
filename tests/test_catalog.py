import json

import pytest

from conftest import edited
from skyroll_demo import catalog
from skyroll_demo.catalog import CatalogError


def test_example_catalog_has_20_elements(cat):
    assert len(cat.elements) == 20


def test_every_behaviour_is_known(cat):
    assert {e["comportament"] for e in cat.elements.values()} <= catalog.BEHAVIOURS


def test_dependencies_are_derived_from_arguments(cat):
    assert cat.deps["Venit net"] == {"Venit brut realizat", "CAS Angajat", "CASS Angajat"}
    assert cat.deps["Suma Ore Lucrate"] == {"Ore Lucrate", "Salariu brut lei", "Ore lucratoare in luna"}


def test_sum_components_come_from_intra_in(cat):
    assert cat.components_of("Venit brut realizat") == ["Suma Ore Lucrate", "Suma ore suplimentare", "Bonus"]


def test_order_puts_every_dependency_first(cat):
    pos = {n: i for i, n in enumerate(cat.order)}
    for name, deps in cat.deps.items():
        for d in deps:
            if d in pos:
                assert pos[d] < pos[name], (d, name)


def test_order_is_the_same_whatever_the_catalog_order(raw_catalog):
    shuffled = dict(raw_catalog, elemente=list(reversed(raw_catalog["elemente"])))
    assert catalog.from_dict(shuffled).order == catalog.from_dict(raw_catalog).order


def test_cycle_is_refused(raw_catalog):
    vn = next(e for e in raw_catalog["elemente"] if e["nume"] == "Venit net")
    terms = vn["argumente"]["formula"] + [{"element": "Salariu net", "semn": "-"}]
    looped = dict(vn, argumente={"formula": terms, "rotunjire": None})
    with pytest.raises(CatalogError, match="cycle"):
        catalog.from_dict(edited(raw_catalog, **{"Venit net": looped}))


def test_unknown_behaviour_is_refused(raw_catalog):
    with pytest.raises(CatalogError, match="unknown behaviour"):
        catalog.from_dict(edited(raw_catalog, Bonus={"nume": "Bonus", "comportament": "magic"}))


def test_missing_argument_is_refused(raw_catalog):
    cas = next(e for e in raw_catalog["elemente"] if e["nume"] == "CAS Angajat")
    broken = dict(cas, argumente={"baza_formula": cas["argumente"]["baza_formula"], "rotunjire": 0})
    with pytest.raises(CatalogError, match="missing arguments"):
        catalog.from_dict(edited(raw_catalog, **{"CAS Angajat": broken}))


def test_reference_to_unknown_element_is_refused(raw_catalog):
    with pytest.raises(CatalogError, match="unknown element 'Prima'"):
        catalog.from_dict(edited(raw_catalog, Bonus={"nume": "Bonus", "comportament": "input",
                                                     "intra_in": {"element": "Prima"}}))


def test_add_element_writes_a_valid_catalog(tmp_path, raw_catalog):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(raw_catalog), encoding="utf-8")
    new = {"nume": "Prima vacanta", "comportament": "input", "intra_in": {"element": "Venit brut realizat"}}
    cat = catalog.add_element(str(path), new)
    assert "Prima vacanta" in cat.components_of("Venit brut realizat")
    assert "Prima vacanta" in catalog.load(str(path)).elements


def test_add_element_leaves_the_file_untouched_when_invalid(tmp_path, raw_catalog):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(raw_catalog), encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(CatalogError):
        catalog.add_element(str(path), {"nume": "Bonus", "comportament": "input"})   # declared twice
    assert path.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["catalog.json"]

import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from skyroll_demo import CATALOG, PARAMETERS, catalog, sintetic  # noqa: E402
from skyroll_demo.parametri import Store  # noqa: E402
from skyroll_demo.stat import Statement  # noqa: E402


@pytest.fixture
def raw_catalog():
    with open(CATALOG, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def cat(raw_catalog):
    return catalog.from_dict(raw_catalog)


@pytest.fixture
def params():
    return Store.load(PARAMETERS)


@pytest.fixture
def statement(params):
    headers, rows = sintetic.build(params)
    return Statement(headers=headers, rows=rows)


@pytest.fixture
def clean_statement(params):
    headers, rows = sintetic.build(params, with_mistakes=False)
    return Statement(headers=headers, rows=rows)


def edited(raw, **changes):
    """A deep copy of the catalog with some elements replaced (name -> element or None)."""
    raw = copy.deepcopy(raw)
    els = []
    for e in raw["elemente"]:
        if e["nume"] in changes:
            if changes[e["nume"]] is not None:
                els.append(changes[e["nume"]])
        else:
            els.append(e)
    raw["elemente"] = els
    return raw

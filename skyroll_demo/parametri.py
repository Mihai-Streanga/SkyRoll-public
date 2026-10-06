"""The parameter store: the values the law (or the employer) sets, each with a validity interval.

The catalog says *what* is calculated; parameters say *with which values, from when*.
A change in the law is a new parameter entry with a start date; the catalog and the
code stay as they are, and an older month still uses the values valid at the time.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date


class ParameterError(LookupError):
    """No value (or more than one) is valid for the month being checked."""


@dataclass(frozen=True)
class Parameter:
    nume: str
    valoare: float
    de_la: date
    pana_la: date | None
    sursa: str


def _d(text: str | None) -> date | None:
    return date.fromisoformat(text) if text else None


class Store:
    def __init__(self, entries: list[Parameter]):
        self.entries = entries

    @classmethod
    def load(cls, path: str) -> "Store":
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        return cls([Parameter(e["nume"], e["valoare"], _d(e["de_la"]), _d(e.get("pana_la")),
                              e.get("sursa", "")) for e in raw])

    def value(self, name: str, month: date) -> float:
        """The single value of `name` valid on the first day of `month`."""
        day = date(month.year, month.month, 1)
        valid = [p for p in self.entries
                 if p.nume == name and p.de_la <= day and (p.pana_la is None or day <= p.pana_la)]
        if not valid:
            raise ParameterError(f"no value for '{name}' valid in {day:%Y-%m}")
        if len(valid) > 1:
            raise ParameterError(f"{len(valid)} overlapping values for '{name}' in {day:%Y-%m}")
        return valid[0].valoare

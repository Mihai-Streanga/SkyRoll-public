"""The catalog: the single description of what a payroll statement contains.

The engine knows no column names. Every element of the statement (a column) is
described here by a name and a behaviour; the behaviour decides how the element is
recalculated, and its arguments name the other elements it depends on. A new column
becomes a new catalog entry, not new code.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field

# Behaviours that only carry data from the statement.
PASSIVE = {"cheie", "operand", "input"}
# Behaviours that are recalculated and compared with the statement.
COMPUTED = {"suma_pontaj", "tichete", "suma_componente", "formula", "cota", "rest_plata"}
BEHAVIOURS = PASSIVE | COMPUTED

# Arguments each computed behaviour must declare, and which of them name elements.
REQUIRED_ARGS = {
    "suma_pontaj": ("operand", "salariu", "norma", "spor_implicit", "spor_param", "rotunjire"),
    "tichete": ("nr", "valoare_param", "rotunjire"),
    "suma_componente": ("rotunjire",),
    "formula": ("formula", "rotunjire"),
    "cota": ("baza_formula", "cota_param", "rotunjire"),
    "rest_plata": ("net", "rotunjire"),
}
ELEMENT_ARGS = {
    "suma_pontaj": ("operand", "salariu", "norma"),
    "tichete": ("nr",),
    "rest_plata": ("net",),
}
TERM_ARGS = {"formula": "formula", "cota": "baza_formula"}


class CatalogError(ValueError):
    """The catalog is not usable: the engine refuses to run on it."""


@dataclass
class Catalog:
    elements: dict[str, dict]
    order: list[str] = field(default_factory=list)     # computed elements, dependency order
    deps: dict[str, set[str]] = field(default_factory=dict)

    def computed(self) -> list[str]:
        return list(self.order)

    def fundamental(self) -> list[str]:
        return [n for n, e in self.elements.items() if e.get("fundamental")]

    def components_of(self, name: str) -> list[str]:
        """Elements that declare themselves part of `name` (intra_in), in catalog order."""
        return [n for n, e in self.elements.items()
                if (e.get("intra_in") or {}).get("element") == name]


def _terms(element: dict) -> list[str]:
    key = TERM_ARGS.get(element["comportament"])
    if not key:
        return []
    return [t.get("element") for t in (element.get("argumente") or {}).get(key) or []]


def validate(raw: dict) -> dict[str, dict]:
    """Check the catalog structure; return the elements by name. Raises CatalogError."""
    if not isinstance(raw, dict) or not isinstance(raw.get("elemente"), list):
        raise CatalogError("catalog must be an object with an 'elemente' list")
    elements: dict[str, dict] = {}
    problems: list[str] = []
    for i, e in enumerate(raw["elemente"]):
        name = e.get("nume")
        if not isinstance(name, str) or not name.strip():
            problems.append(f"element {i}: missing 'nume'")
            continue
        if name in elements:
            problems.append(f"'{name}': declared twice")
            continue
        beh = e.get("comportament")
        if beh not in BEHAVIOURS:
            problems.append(f"'{name}': unknown behaviour '{beh}'")
            continue
        if beh in COMPUTED:
            args = e.get("argumente") or {}
            missing = [a for a in REQUIRED_ARGS[beh] if a not in args]
            if missing:
                problems.append(f"'{name}': missing arguments {missing}")
            if not isinstance(e.get("toleranta"), (int, float)) or e["toleranta"] < 0:
                problems.append(f"'{name}': 'toleranta' must be a number >= 0")
            if not e.get("mesaj"):
                problems.append(f"'{name}': missing 'mesaj'")
            for term in args.get(TERM_ARGS.get(beh, ""), []) or []:
                if term.get("semn") not in ("+", "-"):
                    problems.append(f"'{name}': term '{term.get('element')}' needs semn '+' or '-'")
        elements[name] = e
    for name, e in elements.items():
        refs = list(_terms(e))
        args = e.get("argumente") or {}
        refs += [args[a] for a in ELEMENT_ARGS.get(e["comportament"], ()) if a in args]
        target = (e.get("intra_in") or {}).get("element")
        if target is not None:
            refs.append(target)
            if target in elements and elements[target]["comportament"] != "suma_componente":
                problems.append(f"'{name}': intra_in points to '{target}', which is not a suma_componente")
        for r in refs:
            if r not in elements:
                problems.append(f"'{name}': refers to unknown element '{r}'")
    if problems:
        raise CatalogError("; ".join(problems))
    return elements


def dependencies(elements: dict[str, dict]) -> dict[str, set[str]]:
    """Derived from the arguments, never written by hand."""
    deps: dict[str, set[str]] = {}
    for name, e in elements.items():
        if e["comportament"] not in COMPUTED:
            continue
        args = e["argumente"]
        d = set(_terms(e))
        d |= {args[a] for a in ELEMENT_ARGS.get(e["comportament"], ())}
        if e["comportament"] == "suma_componente":
            d |= {n for n, x in elements.items() if (x.get("intra_in") or {}).get("element") == name}
        deps[name] = d
    return deps


def topological_order(elements: dict[str, dict], deps: dict[str, set[str]]) -> list[str]:
    """Each computed element after the computed elements it depends on.

    Ties are broken alphabetically, so the order is the same on every run and every
    machine (iterating a set directly would not be). A cycle stops the engine.
    """
    done: set[str] = set()
    order: list[str] = []

    def visit(name: str, stack: list[str]) -> None:
        if name in done:
            return
        if name in stack:
            raise CatalogError("dependency cycle: " + " -> ".join(stack + [name]))
        stack.append(name)
        for dep in sorted(deps.get(name, ())):
            if dep in deps:
                visit(dep, stack)
        stack.pop()
        done.add(name)
        order.append(name)

    for name in sorted(deps):
        visit(name, [])
    return order


def from_dict(raw: dict) -> Catalog:
    elements = validate(raw)
    deps = dependencies(elements)
    return Catalog(elements=elements, order=topological_order(elements, deps), deps=deps)


def load(path: str) -> Catalog:
    with open(path, encoding="utf-8") as f:
        return from_dict(json.load(f))


def add_element(path: str, element: dict) -> Catalog:
    """Onboarding: add one element to the catalog file, safely.

    The new catalog is validated in memory first; only a valid catalog is written,
    through a temporary file and an atomic replace, so the file on disk is never
    left half-written or invalid.
    """
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    raw = {**raw, "elemente": raw["elemente"] + [element]}
    catalog = from_dict(raw)                      # raises before anything is written
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".catalog-", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return catalog

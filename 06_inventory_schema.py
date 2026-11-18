#!/usr/bin/env python3
"""06_inventory_schema.py — Chapter 6 companion.

Artefact, MaterialityAssessment, ValidationRecord, SystemEntry dataclasses;
ModelInventory container with a flexible query() method; populated with the
three Chapter 5 case studies; five worked queries plus a portfolio summary.
Standard library only. Reuses the Ch 5 extractor and the Ch 3 scoper by
import-equivalent inline definitions.
"""
from dataclasses import dataclass, field
from datetime import date
import importlib.util, pathlib, sys

def _load(name):
    p = pathlib.Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name.lstrip("0123456789_") or name, p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

m05 = _load("05_inventory_artefacts")

@dataclass
class MaterialityAssessment:
    inherent_risk: str   # LOW/MEDIUM/HIGH
    exposure: str
    purpose: str         # informational / decision-support / decisioning
    tier: str            # T1..T3

@dataclass
class ValidationRecord:
    last_validated: date
    outcome: str         # PASS / CONDITIONAL / FAIL / PENDING
    validator: str

@dataclass
class SystemEntry:
    system_id: str
    name: str
    artefacts: list
    materiality: MaterialityAssessment
    validation: ValidationRecord
    regulatory_scope: list

@dataclass
class ModelInventory:
    entries: list = field(default_factory=list)

    def add(self, e): self.entries.append(e)

    def query(self, **preds):
        out = self.entries
        for k, v in preds.items():
            out = [e for e in out
                   if (getattr(e.materiality, k, None) == v)
                   or (getattr(e.validation, k, None) == v)
                   or (getattr(e, k, None) == v)
                   or (callable(v) and v(e))]
        return out

def build() -> ModelInventory:
    inv = ModelInventory()
    specs = {
        "chatbot": (m05.CASES[0], MaterialityAssessment("MEDIUM", "HIGH", "informational", "T2"),
                    ValidationRecord(date(2026, 3, 12), "PASS", "A. Levi"),
                    ["Consumer Duty", "SS1/23", "AI Act Art 50"]),
        "summariser": (m05.CASES[1], MaterialityAssessment("HIGH", "HIGH", "decision-support", "T1"),
                       ValidationRecord(date(2026, 5, 2), "CONDITIONAL", "A. Levi"),
                       ["SS1/23", "SM&CR"]),
        "kyc-agent": (m05.CASES[2], MaterialityAssessment("HIGH", "MEDIUM", "decisioning", "T1"),
                      ValidationRecord(date(2025, 11, 20), "PENDING", "unassigned"),
                      ["SS1/23", "UK GDPR Art 22", "BSA/AML principles"]),
    }
    for i, (name, (desc, mat, val, scope)) in enumerate(specs.items(), 1):
        inv.add(SystemEntry(f"SYS-{i:03d}", name, m05.inventory_artefacts(desc), mat, val, scope))
    return inv

def main() -> None:
    print("=" * 72)
    print("06_inventory_schema — the inventory as a queryable object")
    print("=" * 72)
    inv = build()
    print(f"\n[population] {len(inv.entries)} systems, "
          f"{sum(len(e.artefacts) for e in inv.entries)} artefacts")

    queries = [
        ("Tier-1 systems", dict(tier="T1")),
        ("Decisioning-purpose systems", dict(purpose="decisioning")),
        ("Validation outcome CONDITIONAL", dict(outcome="CONDITIONAL")),
        ("Systems with agent tools", dict(f=lambda e: any(a.cls == "agent_tool" for a in e.artefacts))),
        ("Stale validation (>6 months at 2026-07-14)", dict(g=lambda e: (date(2026, 7, 14) - e.validation.last_validated).days > 183)),
    ]
    for i, (label, pred) in enumerate(queries, 1):
        hits = inv.query(**pred)
        print(f"\n[query {i}] {label}: {[e.name for e in hits]}")

    print("\n[portfolio summary]")
    for e in inv.entries:
        print(f"    {e.system_id} {e.name:<11} tier={e.materiality.tier} purpose={e.materiality.purpose:<16} "
              f"artefacts={len(e.artefacts):>2} validation={e.validation.outcome:<11} scope={len(e.regulatory_scope)} regimes")
    print("\nIn production the Ch 5 extractor and Ch 3 scoper run on add and on every attribute change.")

if __name__ == "__main__":
    main()

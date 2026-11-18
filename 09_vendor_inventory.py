#!/usr/bin/env python3
"""09_vendor_inventory.py — Chapter 9 companion.

VendorEntry (risk tier, layer, contractual provisions, due-diligence dates,
supported systems); ContractualProvisions with the ten-provision checklist
and the four-provision LLM minimum; VendorInventory with by-layer, by-tier,
overdue-due-diligence, and inadequate-contract queries; concentration_analysis
computing per-layer vendor share. Standard library only.
"""
from dataclasses import dataclass, field
from datetime import date

TEN_PROVISIONS = ["version_pinning", "change_notice", "deprecation_notice", "audit_rights",
                  "data_residency", "no_training_on_firm_data", "sla_availability",
                  "incident_notification", "exit_assistance", "subprocessor_disclosure"]
LLM_MINIMUM = ["version_pinning", "change_notice", "deprecation_notice", "no_training_on_firm_data"]

@dataclass
class ContractualProvisions:
    granted: set

    def adequate_llm_minimum(self) -> bool:
        return set(LLM_MINIMUM) <= self.granted

    def missing(self):
        return [p for p in TEN_PROVISIONS if p not in self.granted]

@dataclass
class VendorEntry:
    name: str
    layer: str                       # foundation_model / embedding / agent_tool / hosting
    tier: str                        # LOW / MEDIUM / HIGH / CRITICAL
    provisions: ContractualProvisions
    last_due_diligence: date
    supports_systems: list

@dataclass
class VendorInventory:
    vendors: list = field(default_factory=list)

    def by_layer(self, layer): return [v for v in self.vendors if v.layer == layer]
    def by_tier(self, tier): return [v for v in self.vendors if v.tier == tier]

    def overdue_due_diligence(self, today: date, max_days=365):
        return [v for v in self.vendors if (today - v.last_due_diligence).days > max_days]

    def inadequate_contracts(self):
        return [v for v in self.vendors if not v.provisions.adequate_llm_minimum()]

    def concentration_analysis(self, threshold=0.5):
        report = {}
        layers = {v.layer for v in self.vendors}
        for layer in sorted(layers):
            vs = self.by_layer(layer)
            total = sum(len(v.supports_systems) for v in vs) or 1
            shares = {v.name: len(v.supports_systems) / total for v in vs}
            flagged = {k: s for k, s in shares.items() if s >= threshold}
            report[layer] = {"shares": shares, "concentration_flag": flagged}
        return report

def main() -> None:
    print("=" * 72)
    print("09_vendor_inventory — the vendor stack as a governed object")
    print("=" * 72)
    today = date(2026, 7, 14)
    inv = VendorInventory([
        VendorEntry("VendorA", "foundation_model", "CRITICAL",
                    ContractualProvisions(set(TEN_PROVISIONS)),
                    date(2026, 2, 10), ["chatbot", "summariser", "kyc-agent"]),
        VendorEntry("VendorB", "foundation_model", "HIGH",
                    ContractualProvisions({"change_notice", "sla_availability", "data_residency"}),
                    date(2025, 4, 1), ["triage-poc"]),
        VendorEntry("ToolCo", "agent_tool", "MEDIUM",
                    ContractualProvisions({"version_pinning", "change_notice", "deprecation_notice",
                                           "no_training_on_firm_data", "incident_notification"}),
                    date(2026, 6, 5), ["kyc-agent"]),
    ])

    print("\n[1] inventory")
    for v in inv.vendors:
        print(f"    {v.name:<8} layer={v.layer:<16} tier={v.tier:<8} systems={len(v.supports_systems)} "
              f"dd={v.last_due_diligence} llm-minimum={'OK' if v.provisions.adequate_llm_minimum() else 'INADEQUATE'}")

    print("\n[2] queries")
    print(f"    foundation-model layer : {[v.name for v in inv.by_layer('foundation_model')]}")
    print(f"    CRITICAL tier          : {[v.name for v in inv.by_tier('CRITICAL')]}")
    od = inv.overdue_due_diligence(today)
    print(f"    overdue due diligence  : {[v.name for v in od]}")
    bad = inv.inadequate_contracts()
    print(f"    inadequate contracts   : {[(v.name, v.provisions.missing()[:3]) for v in bad]}")
    assert od and od[0].name == "VendorB" and bad and bad[0].name == "VendorB"

    print("\n[3] concentration analysis (flag at >= 50% of layer)")
    rep = inv.concentration_analysis()
    for layer, r in rep.items():
        shares = ", ".join(f"{k}={v:.0%}" for k, v in r["shares"].items())
        flag = ", ".join(r["concentration_flag"]) or "none"
        print(f"    {layer:<16}: {shares}   concentration flag: {flag}")
    assert "VendorA" in rep["foundation_model"]["concentration_flag"]
    print("\nOne query surface replaces three spreadsheets; VendorA's 75% share is the CTP-regime conversation.")

if __name__ == "__main__":
    main()

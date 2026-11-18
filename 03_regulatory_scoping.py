#!/usr/bin/env python3
"""03_regulatory_scoping.py — Chapter 3 companion.

The chapter's decision tree as an executable function: given a structured
use-case description, return the applicable regulatory regimes with
rationales. Four worked examples produce materially different scopes.
Standard library only.
"""
from dataclasses import dataclass, field

@dataclass
class UseCase:
    name: str
    jurisdiction: set          # {"UK","EU","US"}
    retail_customers: bool
    credit_decisioning: bool
    natural_persons_scored: bool
    prudentially_regulated_bank: bool
    us_assets_over_30bn: bool = False
    internal_only: bool = False
    insurance_underwriting: bool = False
    aml_related: bool = False

def regulatory_scope(u: UseCase):
    scope = []
    add = lambda regime, why: scope.append((regime, why))
    if "UK" in u.jurisdiction and u.prudentially_regulated_bank:
        add("PRA SS1/23", "UK PRA-regulated bank: model within Principle 1 definition; principles apply regardless of the US carve-out")
    if "US" in u.jurisdiction:
        if u.us_assets_over_30bn:
            add("SR 26-2 (principles-by-analogy)", "Generative/agentic AI is outside SR 26-2's formal scope; the letter expects the underlying principles to be applied")
        else:
            add("SR 26-2 (voluntary benchmark)", "Below the $30bn relevance threshold; guidance remains the examination benchmark in practice")
    if "EU" in u.jurisdiction:
        if u.credit_decisioning and u.natural_persons_scored:
            add("EU AI Act — Annex III high-risk (5(b))", "Creditworthiness scoring of natural persons; high-risk obligations apply from 2 Dec 2027 (Digital Omnibus)")
        elif u.insurance_underwriting:
            add("EU AI Act — Annex III high-risk (5(c))", "Life/health insurance pricing high-risk category")
        elif not u.internal_only:
            add("EU AI Act — Article 50 transparency", "Customer-facing AI interaction; transparency duties from 2 Aug 2026")
        else:
            add("EU AI Act — minimal risk", "Internal tool outside Annex III; GPAI duties sit with the provider")
    if "UK" in u.jurisdiction and u.retail_customers:
        add("FCA Consumer Duty (PS22/9)", "Retail customers: four-outcomes evidence attaches to the use case")
    if u.credit_decisioning and u.natural_persons_scored and ("UK" in u.jurisdiction or "EU" in u.jurisdiction):
        add("GDPR/UK GDPR Article 22", "Automated decision with legal or similarly significant effect; UK position as amended by DUAA 2025")
        add("Equality Act 2010 s.19" if "UK" in u.jurisdiction else "EU non-discrimination law",
            "Indirect-discrimination exposure through proxy features")
    if u.aml_related:
        add("BSA/AML supervisory expectations", "SR 21-8 rescinded into SR 26-2; AML models covered by the general framework")
    if "UK" in u.jurisdiction:
        add("SM&CR", "Named senior-manager accountability for the model risk framework")
    return scope

CASES = [
    UseCase("Retail credit decisioning assistant", {"UK", "EU"}, True, True, True, True),
    UseCase("AML alert triage", {"US"}, False, False, False, True, us_assets_over_30bn=True, internal_only=True, aml_related=True),
    UseCase("Internal IT support chatbot", {"UK"}, False, False, False, True, internal_only=True),
    UseCase("Insurance underwriting assistant", {"EU"}, True, False, False, False, insurance_underwriting=True),
]

def main() -> None:
    print("=" * 72)
    print("03_regulatory_scoping — one inventory, per-use-case classification")
    print("=" * 72)
    sizes = []
    for c in CASES:
        s = regulatory_scope(c)
        sizes.append(len(s))
        print(f"\n{c.name}  ({', '.join(sorted(c.jurisdiction))})")
        for regime, why in s:
            print(f"    - {regime}\n        {why}")
    assert len(set(sizes)) > 1, "cases should produce materially different scopes"
    print("\nFour use cases, four different regulatory scopes — a blanket rating cannot capture this.")

if __name__ == "__main__":
    main()

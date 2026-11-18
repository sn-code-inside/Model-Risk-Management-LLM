#!/usr/bin/env python3
"""19_per_deal_evidence.py — Chapter 19 companion.

Deal dataclass with deal-type and per-metric labelled outcomes; DealType
enum; make_sample() reconstructing the 80-deal Figure 19.3 sample;
evaluate_per_deal_type() producing per-type evidence rows with min-metric
and approve/conditional/reject classification; deployment-recommendation
block. Reproduces Figure 19.3 exactly: working-capital, term-loan,
asset-finance -> approve; trade-finance -> conditional (HITL every case);
project-finance, restructuring -> reject. Standard library only.
"""
from dataclasses import dataclass
from enum import Enum

class DealType(Enum):
    WORKING_CAPITAL = "working_capital"
    TERM_LOAN = "term_loan"
    ASSET_FINANCE = "asset_finance"
    TRADE_FINANCE = "trade_finance"
    PROJECT_FINANCE = "project_finance"
    RESTRUCTURING = "restructuring"

@dataclass
class Deal:
    deal_id: int
    deal_type: DealType
    covenant_extraction_ok: bool
    exposure_figures_ok: bool
    risk_narrative_ok: bool

# (n, covenant_ok, exposure_ok, narrative_ok) per type — constructed to Figure 19.3
SPEC = {DealType.WORKING_CAPITAL: (20, 19, 20, 18),   # min 90%
        DealType.TERM_LOAN:       (18, 17, 17, 17),   # min 94%
        DealType.ASSET_FINANCE:   (14, 13, 14, 13),   # min 93%
        DealType.TRADE_FINANCE:   (12, 10, 11, 9),    # min 75%  -> conditional
        DealType.PROJECT_FINANCE: (10, 6, 7, 5),      # min 50%  -> reject
        DealType.RESTRUCTURING:   (6, 3, 4, 2)}       # min 33%  -> reject

PROD_SHARE = {DealType.WORKING_CAPITAL: 0.34, DealType.TERM_LOAN: 0.27, DealType.ASSET_FINANCE: 0.18,
              DealType.TRADE_FINANCE: 0.12, DealType.PROJECT_FINANCE: 0.06, DealType.RESTRUCTURING: 0.03}

def make_sample():
    deals, did = [], 0
    for dt, (n, c, e, r) in SPEC.items():
        for i in range(n):
            deals.append(Deal(did, dt, i < c, i < e, i < r)); did += 1
    return deals

def evaluate_per_deal_type(deals, approve_at=0.85, conditional_at=0.70):
    rows = []
    for dt in DealType:
        sub = [d for d in deals if d.deal_type == dt]
        n = len(sub)
        cov = sum(d.covenant_extraction_ok for d in sub) / n
        exp = sum(d.exposure_figures_ok for d in sub) / n
        nar = sum(d.risk_narrative_ok for d in sub) / n
        mn = min(cov, exp, nar)
        cls = "approve" if mn >= approve_at else "conditional" if mn >= conditional_at else "reject"
        rows.append({"deal_type": dt, "n": n, "covenant": cov, "exposure": exp,
                     "narrative": nar, "min_metric": mn, "classification": cls,
                     "prod_share": PROD_SHARE[dt]})
    return rows

def main() -> None:
    print("=" * 72)
    print("19_per_deal_evidence — the per-deal-type evidence pattern (Fig. 19.3)")
    print("=" * 72)
    deals = make_sample()
    assert len(deals) == 80
    rows = evaluate_per_deal_type(deals)

    print(f"\n[1] per-type evidence rows ({len(deals)} deals)")
    for r in rows:
        print(f"    {r['deal_type'].value:<16} n={r['n']:>2} share={r['prod_share']:.0%}  "
              f"cov={r['covenant']:.2f} exp={r['exposure']:.2f} nar={r['narrative']:.2f}  "
              f"min={r['min_metric']:.2f} -> {r['classification'].upper()}")

    got = {r["deal_type"]: r["classification"] for r in rows}
    assert got == {DealType.WORKING_CAPITAL: "approve", DealType.TERM_LOAN: "approve",
                   DealType.ASSET_FINANCE: "approve", DealType.TRADE_FINANCE: "conditional",
                   DealType.PROJECT_FINANCE: "reject", DealType.RESTRUCTURING: "reject"}, got

    print("\n[2] why the pooled headline misleads")
    total_ok = sum(min(d.covenant_extraction_ok, d.exposure_figures_ok, d.risk_narrative_ok) for d in deals)
    print(f"    pooled all-metrics-ok rate: {total_ok/len(deals):.1%} — dominated by the types where the system works")

    print("\n[3] deployment recommendation (goes into the validation file)")
    print("    APPROVE      : working_capital, term_loan, asset_finance")
    print("    CONDITIONAL  : trade_finance — HITL review on every case; re-evaluate at n>=30")
    print("    REJECT       : project_finance, restructuring — route to human drafting; no LLM output")

if __name__ == "__main__":
    main()

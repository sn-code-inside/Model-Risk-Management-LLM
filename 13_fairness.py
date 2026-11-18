#!/usr/bin/env python3
"""13_fairness.py — Chapter 13 companion.

Per-group selection_rate/tpr/fpr; demographic_parity_diff and
equalised_odds_max_diff with bootstrap CIs; per-group ECE for calibration
parity; ConsumerDutyEvidence with consumer_duty_summary. Demonstrates the
impossibility result by example: DP fails at a 5pp threshold while
equalised odds passes on the same dataset. numpy only.
"""
import numpy as np
from dataclasses import dataclass

rng = np.random.default_rng(13)

def selection_rate(pred): return float(np.mean(pred))
def tpr(pred, y): return float(pred[y == 1].mean()) if (y == 1).any() else float("nan")
def fpr(pred, y): return float(pred[y == 0].mean()) if (y == 0).any() else float("nan")

def demographic_parity_diff(pred, group):
    return abs(selection_rate(pred[group == 0]) - selection_rate(pred[group == 1]))

def equalised_odds_max_diff(pred, y, group):
    d_tpr = abs(tpr(pred[group == 0], y[group == 0]) - tpr(pred[group == 1], y[group == 1]))
    d_fpr = abs(fpr(pred[group == 0], y[group == 0]) - fpr(pred[group == 1], y[group == 1]))
    return max(d_tpr, d_fpr)

def bootstrap_ci(fn, data, B=1000, seed=0):
    r = np.random.default_rng(seed); n = len(data[0])
    vals = [fn(*(d[idx] for d in data)) for idx in (r.integers(0, n, n) for _ in range(B))]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))

def group_ece(probs, correct, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1); ece, n = 0.0, len(probs)
    for b in range(n_bins):
        m = (probs >= bins[b]) & (probs < bins[b + 1])
        if b == n_bins - 1: m |= probs == 1.0
        if m.sum(): ece += m.sum() / n * abs(correct[m].mean() - probs[m].mean())
    return float(ece)

@dataclass
class ConsumerDutyEvidence:
    products_and_services: bool
    price_and_value: bool
    consumer_understanding: bool
    consumer_support: bool
    notes: dict

def consumer_duty_summary(e: ConsumerDutyEvidence):
    outcomes = {"Products and services": e.products_and_services,
                "Price and value": e.price_and_value,
                "Consumer understanding": e.consumer_understanding,
                "Consumer support": e.consumer_support}
    return outcomes, all(outcomes.values())

def main() -> None:
    print("=" * 72)
    print("13_fairness — three criteria, one dataset, and why they cannot all hold")
    print("=" * 72)

    # two groups with different base rates: qualification differs, calibrated scorer
    n0, n1 = 3000, 3000
    y0 = (rng.random(n0) < 0.55).astype(int)      # group 0 base rate 55%
    y1 = (rng.random(n1) < 0.35).astype(int)      # group 1 base rate 35%
    def score(y): return np.clip(0.35 + 0.4 * y + rng.normal(0, 0.13, len(y)), 0, 1)
    s0, s1 = score(y0), score(y1)
    t = 0.55
    p0, p1 = (s0 >= t).astype(int), (s1 >= t).astype(int)
    pred = np.concatenate([p0, p1]); y = np.concatenate([y0, y1])
    grp = np.concatenate([np.zeros(n0, int), np.ones(n1, int)])
    probs = np.concatenate([s0, s1])

    print("\n[1] per-group primitives")
    for g in (0, 1):
        m = grp == g
        print(f"    group {g}: base rate={y[m].mean():.3f} selection={selection_rate(pred[m]):.3f} "
              f"TPR={tpr(pred[m], y[m]):.3f} FPR={fpr(pred[m], y[m]):.3f}")

    print("\n[2] the three criteria with bootstrap CIs (threshold: 5pp)")
    dp = demographic_parity_diff(pred, grp)
    dplo, dphi = bootstrap_ci(lambda p, g: demographic_parity_diff(p, g), (pred, grp), seed=1)
    eo = equalised_odds_max_diff(pred, y, grp)
    eolo, eohi = bootstrap_ci(lambda p, yy, g: equalised_odds_max_diff(p, yy, g), (pred, y, grp), seed=2)
    e0 = group_ece(probs[grp == 0], y[grp == 0]); e1 = group_ece(probs[grp == 1], y[grp == 1])
    print(f"    demographic parity diff : {dp:.3f}  CI [{dplo:.3f},{dphi:.3f}]  -> {'FAIL' if dp > 0.05 else 'pass'} at 5pp")
    print(f"    equalised odds max diff : {eo:.3f}  CI [{eolo:.3f},{eohi:.3f}]  -> {'FAIL' if eo > 0.05 else 'PASS'} at 5pp")
    print(f"    calibration parity ECE  : group0={e0:.3f} group1={e1:.3f} |diff|={abs(e0-e1):.3f}")
    assert dp > 0.05 and eo <= 0.05, (dp, eo)
    print("    Same dataset, same scorer: DP fails while EO passes — Chouldechova/Kleinberg by example.")

    print("\n[3] Consumer Duty checklist on the retail chatbot")
    ev = ConsumerDutyEvidence(False, True, True, False,
                              {"Products and services": "no target-market appropriateness testing",
                               "Consumer support": "vulnerable-segment accuracy 79% vs 85% threshold"})
    outcomes, overall = consumer_duty_summary(ev)
    for k, v in outcomes.items():
        note = f" — {ev.notes[k]}" if not v and k in ev.notes else ""
        print(f"    {k:<24}: {'PASS' if v else 'FAIL'}{note}")
    print(f"    overall: {'PASS' if overall else 'BLOCKED'}")
    assert not overall

if __name__ == "__main__":
    main()

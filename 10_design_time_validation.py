#!/usr/bin/env python3
"""10_design_time_validation.py — Chapter 10 companion.

Segment enum and TestCase dataclass; generate_population (5,000 synthetic
cases matching the production distribution); stratify to per-segment quotas;
find_min_cost_threshold; evaluate_per_segment with CIs; headline_accuracy
under multiple weightings. Reproduces the headline-vs-segment trap:
production-weighted 87.5% vs uniform-segment 71.8%. Standard library only.
"""
import math, random
from dataclasses import dataclass
from enum import Enum

class Segment(Enum):
    MAINSTREAM = "mainstream"
    THIN_FILE = "thin_file"
    SELF_EMPLOYED = "self_employed"
    NEW_PRODUCT = "new_product"
    VULNERABLE = "vulnerable"

# production distribution (78-10-7-3-2) and constructed per-segment correctness
POP = {Segment.MAINSTREAM: (3900, 3519),   # 90.23%
       Segment.THIN_FILE: (500, 450),      # 90.00%
       Segment.SELF_EMPLOYED: (350, 280),  # 80.00%
       Segment.NEW_PRODUCT: (150, 82),     # 54.67%
       Segment.VULNERABLE: (100, 44)}      # 44.00%

@dataclass
class TestCase:
    case_id: int
    segment: Segment
    correct: bool

def generate_population():
    cases, cid = [], 0
    for seg, (n, k) in POP.items():
        for i in range(n):
            cases.append(TestCase(cid, seg, i < k)); cid += 1
    rnd = random.Random(10); rnd.shuffle(cases)
    return cases

def stratify(population, quotas):
    rnd = random.Random(20)
    out = []
    by_seg = {s: [c for c in population if c.segment == s] for s in Segment}
    for seg, q in quotas.items():
        out.extend(rnd.sample(by_seg[seg], q))
    return out

def wilson_halfwidth(p, n, z=1.96):
    if n == 0: return float("nan")
    return z * math.sqrt(p * (1 - p) / n)

def evaluate_per_segment(cases):
    rep = {}
    for seg in Segment:
        sub = [c for c in cases if c.segment == seg]
        n = len(sub)
        p = sum(c.correct for c in sub) / n if n else float("nan")
        rep[seg] = (n, p, wilson_halfwidth(p, n) if n else float("nan"))
    return rep

def headline_accuracy(rep, weighting="production", weights=None):
    if weighting == "production":
        total = sum(POP[s][0] for s in Segment)
        return sum(POP[s][0] / total * rep[s][1] for s in Segment)
    if weighting == "uniform":
        return sum(rep[s][1] for s in Segment) / len(Segment)
    return sum(weights[s] * rep[s][1] for s in Segment)

def find_min_cost_threshold(k_ratio=5.0):
    """Sweep thresholds on a synthetic score distribution; FN costs k_ratio x FP."""
    rnd = random.Random(30)
    pos = [min(1, max(0, rnd.gauss(0.72, 0.13))) for _ in range(2000)]
    neg = [min(1, max(0, rnd.gauss(0.38, 0.15))) for _ in range(2000)]
    best = None
    for t in [i / 100 for i in range(5, 96)]:
        fn = sum(p < t for p in pos)
        fp = sum(q >= t for q in neg)
        cost = k_ratio * fn + fp
        if best is None or cost < best[1]:
            best = (t, cost, fn, fp)
    return best

def main() -> None:
    print("=" * 72)
    print("10_design_time_validation — stratification, thresholds, and the headline trap")
    print("=" * 72)
    pop = generate_population()
    print(f"\n[1] population: {len(pop)} cases across {len(Segment)} segments (78-10-7-3-2)")

    full = evaluate_per_segment(pop)
    prod = headline_accuracy(full, "production")
    unif = headline_accuracy(full, "uniform")
    print("\n[2] the headline-vs-segment trap, on the full population")
    for s in Segment:
        n, p, hw = full[s]
        print(f"    {s.value:<14} n={n:>4}  acc={p:6.3f}  ±{hw:.3f}")
    print(f"    production-weighted headline: {prod:.3%}")
    print(f"    uniform-segment headline    : {unif:.3%}")
    assert abs(prod - 0.875) < 1e-9, prod
    assert abs(unif - 0.71779) < 5e-4, unif

    print("\n[3] naive 200-case sample (production-proportional) vs stratified 40-20-15-15-10%")
    naive = stratify(pop, {Segment.MAINSTREAM: 156, Segment.THIN_FILE: 20, Segment.SELF_EMPLOYED: 14,
                           Segment.NEW_PRODUCT: 6, Segment.VULNERABLE: 4})
    strat = stratify(pop, {Segment.MAINSTREAM: 80, Segment.THIN_FILE: 40, Segment.SELF_EMPLOYED: 30,
                           Segment.NEW_PRODUCT: 30, Segment.VULNERABLE: 20})
    strat2 = stratify(pop, {Segment.MAINSTREAM: 80, Segment.THIN_FILE: 40, Segment.SELF_EMPLOYED: 30,
                            Segment.NEW_PRODUCT: 10, Segment.VULNERABLE: 40})
    for label, sample in (("naive-200", naive), ("stratified-200", strat), ("quota-first-200 (40 vulnerable)", strat2)):
        rep = evaluate_per_segment(sample)
        n, p, hw = rep[Segment.VULNERABLE]
        print(f"    {label:<32} vulnerable: n={n:>3} acc={p:5.3f} ±{hw:.3f}"
              f"{'  <- too noisy for 2LoD review' if hw > 0.09 else ''}")
    print("    The rule works backwards from per-segment interval targets to the total, not forwards.")

    print("\n[4] find_min_cost_threshold at K=5 (an FN costs five FPs)")
    t, cost, fn, fp = find_min_cost_threshold(5.0)
    print(f"    minimum-cost threshold t*={t:.2f}  (cost={cost}, FN={fn}, FP={fp})")

if __name__ == "__main__":
    main()

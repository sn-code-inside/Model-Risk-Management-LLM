#!/usr/bin/env python3
"""11_validation_harness.py — Chapter 11 companion.

Power analysis (required_n); bootstrap CIs on arbitrary metrics
(bootstrap_ci, evaluate); LLM-as-judge calibration with quadratic-weighted
kappa (calibrate_judge, quadratic_weighted_kappa); regression testing
against a frozen baseline (RegressionTest); and — new in v1.1 — the
Section 11.4.6 components-of-variance protocol (variance_components),
estimated by method of moments on a crossed seed-by-paraphrase design.
numpy only; no API keys.
"""
import numpy as np
from dataclasses import dataclass

# --- 11.4: power analysis and the bootstrap -----------------------------------
def required_n(p0=0.85, moe=0.05, z=1.96):
    """n for a proportion CI of half-width moe at worst-case variance near p0."""
    return int(np.ceil(z**2 * p0 * (1 - p0) / moe**2))

def bootstrap_ci(outcomes, metric, B=2000, alpha=0.05, seed=0):
    rng = np.random.default_rng(seed)
    outcomes = np.asarray(outcomes)
    n = len(outcomes)
    boots = np.array([metric(outcomes[rng.integers(0, n, size=n)]) for _ in range(B)])
    return (float(metric(outcomes)),
            float(np.percentile(boots, 100 * alpha / 2)),
            float(np.percentile(boots, 100 * (1 - alpha / 2))))

def evaluate(outcomes, metric=np.mean, threshold=None, direction=">=", **kw):
    v, lo, hi = bootstrap_ci(outcomes, metric, **kw)
    verdict = None
    if threshold is not None:
        verdict = (lo >= threshold) if direction == ">=" else (hi <= threshold)
    return {"value": v, "ci": (lo, hi), "threshold": threshold, "pass": verdict}

# --- 11.6: judge calibration -----------------------------------------------------
def quadratic_weighted_kappa(a, b, k=5):
    a, b = np.asarray(a), np.asarray(b)
    O = np.zeros((k, k))
    for i, j in zip(a, b):
        O[i, j] += 1
    w = np.array([[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)])
    ra, rb = O.sum(1), O.sum(0)
    E = np.outer(ra, rb) / O.sum()
    return float(1 - (w * O).sum() / (w * E).sum())

def calibrate_judge(human, judge):
    kappa = quadratic_weighted_kappa(human, judge)
    bias = float(np.mean(np.asarray(judge) - np.asarray(human)))
    fit = "adequate" if kappa >= 0.6 else "inadequate — judge cannot substitute for human rating"
    return {"kappa": round(kappa, 3), "mean_bias": round(bias, 3), "fit": fit}

# --- 11.7: regression against a frozen baseline -----------------------------------
@dataclass
class RegressionTest:
    baseline: dict            # metric -> (value, n)
    tolerance: float = 0.03

    def run(self, current: dict):
        out = {}
        for m, (bv, n) in self.baseline.items():
            cv = current[m]
            out[m] = {"baseline": bv, "current": cv, "delta": round(cv - bv, 4),
                      "verdict": "REGRESSED" if cv < bv - self.tolerance else "ok"}
        return out

# --- 11.4.6 (v1.1): components of variance ------------------------------------------
def variance_components(metric_grid: np.ndarray):
    """Method-of-moments components on a crossed seed x paraphrase design.

    metric_grid[i, j] is the metric from the run with seed level i and
    paraphrase level j (each cell one full evaluation on the fixed sample).
    Returns additive components: seed, paraphrase, residual (interaction),
    and the non-shrinking share — the fraction of pipeline variance that
    more evaluation cases cannot remove.
    """
    g = np.asarray(metric_grid, float)
    S, P = g.shape
    grand = g.mean()
    ms_seed = P * ((g.mean(axis=1) - grand) ** 2).sum() / (S - 1)
    ms_para = S * ((g.mean(axis=0) - grand) ** 2).sum() / (P - 1)
    resid = g - g.mean(1, keepdims=True) - g.mean(0, keepdims=True) + grand
    ms_res = (resid ** 2).sum() / ((S - 1) * (P - 1))
    var_seed = max(0.0, (ms_seed - ms_res) / P)
    var_para = max(0.0, (ms_para - ms_res) / S)
    total = var_seed + var_para + ms_res
    return {"seed": var_seed, "paraphrase": var_para, "residual": ms_res,
            "total": total,
            "non_shrinking_share": var_para / total if total else 0.0}

# --- demonstrations -------------------------------------------------------------------
def main() -> None:
    rng = np.random.default_rng(1114)
    print("=" * 72)
    print("11_validation_harness — power, bootstrap, judge, regression, variance")
    print("=" * 72)

    print("\n[1] power analysis")
    for moe in (0.05, 0.03, 0.02):
        print(f"    half-width ±{moe:.0%} at p≈0.85 -> n ≥ {required_n(moe=moe)}")

    print("\n[2] bootstrap evaluation on the Figure 11.3 binary classifier (n=400)")
    outcomes = (rng.random(400) < 0.88).astype(int)
    r = evaluate(outcomes, threshold=0.85, seed=3)
    print(f"    accuracy {r['value']:.3f}, 95% CI [{r['ci'][0]:.3f}, {r['ci'][1]:.3f}], "
          f"threshold {r['threshold']} -> {'PASS (CI floor clears threshold)' if r['pass'] else 'NOT DEMONSTRATED'}")

    print("\n[3] LLM-as-judge calibration (Figure 11.4)")
    human = rng.integers(0, 5, size=300)
    judge = np.clip(human + rng.choice([-1, 0, 0, 0, 1], size=300), 0, 4)
    cal = calibrate_judge(human, judge)
    print(f"    quadratic-weighted kappa = {cal['kappa']}  mean bias = {cal['mean_bias']}  -> {cal['fit']}")
    assert cal["kappa"] >= 0.6

    print("\n[4] regression test: simulated vendor-update degradation")
    reg = RegressionTest({"task_accuracy": (0.891, 400), "groundedness": (0.962, 400)})
    degraded = {"task_accuracy": 0.842, "groundedness": 0.958}
    for m, v in reg.run(degraded).items():
        print(f"    {m:<14} baseline={v['baseline']:.3f} current={v['current']:.3f} "
              f"delta={v['delta']:+.3f}  {v['verdict']}")

    print("\n[5] Section 11.4.6: variance_components on a crossed 4-seed x 5-paraphrase design")
    true_acc, sd_seed, sd_para, sd_res = 0.88, 0.006, 0.018, 0.004
    seed_eff = rng.normal(0, sd_seed, 4)
    para_eff = rng.normal(0, sd_para, 5)
    grid = true_acc + seed_eff[:, None] + para_eff[None, :] + rng.normal(0, sd_res, (4, 5))
    vc = variance_components(grid)
    print(f"    component variances: seed={vc['seed']:.2e}  paraphrase={vc['paraphrase']:.2e}  "
          f"residual={vc['residual']:.2e}")
    print(f"    non-shrinking share of pipeline variance: {vc['non_shrinking_share']:.0%}")
    sd_total = float(np.sqrt(vc["total"]))
    _, lo, hi = bootstrap_ci(outcomes, np.mean, seed=4)
    naive_hw = (hi - lo) / 2
    corrected_hw = float(np.sqrt(naive_hw**2 + 1.96**2 * (vc["paraphrase"] + vc["seed"])))
    print(f"    naive CI half-width ±{naive_hw:.3f} -> pipeline-corrected ±{corrected_hw:.3f}")
    print("    The paraphrase component does not shrink with n: a large-n evaluation can be precisely wrong.")
    assert vc["paraphrase"] > vc["seed"], "constructed example: paraphrase dominates"
    print("\nEach block above pastes directly into a validation report.")

if __name__ == "__main__":
    main()

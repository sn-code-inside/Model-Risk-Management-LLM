#!/usr/bin/env python3
"""16_monitoring_harness.py — Chapter 16 companion.

Three-layer architecture: SamplingPolicy (stratified high-risk sampling +
fixed-size reservoir); ControlChart runner (Shewhart-style); PageHinkley
change-point detector; ks_distance for input drift; runbook() returning
structured MonitoringAlert objects. Exercised on 10,000 production calls,
a 90-day accuracy stream with drift, and a shifted-mean drift simulation.
numpy only; reuses the Ch 11 bootstrap pattern.
"""
import numpy as np
from dataclasses import dataclass, field

rng = np.random.default_rng(16)

# --- Layer 1: sampling -----------------------------------------------------------
@dataclass
class SamplingPolicy:
    base_rate: float = 0.02
    high_risk_rate: float = 0.25
    reservoir_size: int = 500

    def sample(self, calls):
        r = np.random.default_rng(161)
        chosen = [c for c in calls
                  if r.random() < (self.high_risk_rate if c["high_risk"] else self.base_rate)]
        # fixed-size reservoir (Vitter's algorithm R)
        res = []
        for i, c in enumerate(chosen):
            if i < self.reservoir_size:
                res.append(c)
            else:
                j = r.integers(0, i + 1)
                if j < self.reservoir_size:
                    res[j] = c
        return chosen, res

# --- Layer 2: detection ------------------------------------------------------------
@dataclass
class ControlChart:
    centre: float
    sigma: float
    k: float = 3.0

    def run(self, stream):
        lo, hi = self.centre - self.k * self.sigma, self.centre + self.k * self.sigma
        return [i for i, x in enumerate(stream) if not (lo <= x <= hi)]

@dataclass
class PageHinkley:
    delta: float = 0.005
    lam: float = 0.05
    _mean: float = 0.0
    _cum: float = 0.0
    _min: float = 0.0
    _n: int = 0

    def update(self, x):
        self._n += 1
        self._mean += (x - self._mean) / self._n
        self._cum += self._mean - x - self.delta       # detect downward shift
        self._min = min(self._min, self._cum)
        return (self._cum - self._min) > self.lam

def ks_distance(a, b):
    a, b = np.sort(a), np.sort(b)
    grid = np.concatenate([a, b])
    Fa = np.searchsorted(a, grid, "right") / len(a)
    Fb = np.searchsorted(b, grid, "right") / len(b)
    return float(np.max(np.abs(Fa - Fb)))

# --- Layer 3: response ----------------------------------------------------------------
@dataclass
class MonitoringAlert:
    source: str
    day: int
    detail: str
    action: str

def runbook(chart_hits, ph_day, ks_stat, ks_threshold=0.1):
    alerts = []
    for d in chart_hits:
        alerts.append(MonitoringAlert("control-chart", d, "point outside 3-sigma limits",
                                      "open incident ticket; freeze prompt/config changes; pull sample for review"))
    if ph_day is not None:
        alerts.append(MonitoringAlert("page-hinkley", ph_day, "sustained downward shift in accuracy",
                                      "trigger Ch 11 regression test against frozen baseline; check vendor changelog"))
    if ks_stat > ks_threshold:
        alerts.append(MonitoringAlert("ks-input-drift", -1, f"KS={ks_stat:.3f} > {ks_threshold}",
                                      "input distribution moved: re-run stratified evaluation before relying on prior evidence"))
    return alerts

def main() -> None:
    print("=" * 72)
    print("16_monitoring_harness — sample, detect, respond")
    print("=" * 72)

    print("\n[1] sampling layer: 10,000 production calls")
    calls = [{"id": i, "high_risk": bool(rng.random() < 0.08)} for i in range(10_000)]
    chosen, reservoir = SamplingPolicy().sample(calls)
    hr = sum(c["high_risk"] for c in chosen)
    print(f"    sampled {len(chosen)} calls ({hr} high-risk, {hr/len(chosen):.0%} of sample vs 8% of traffic)")
    print(f"    review reservoir capped at {len(reservoir)} cases")

    print("\n[2] detection layer: 90-day accuracy stream with a drift from day 60")
    stream = np.concatenate([rng.normal(0.89, 0.012, 60), rng.normal(0.855, 0.012, 30)])
    chart = ControlChart(centre=0.89, sigma=0.012)
    hits = chart.run(stream)
    ph = PageHinkley()
    ph_day = next((i for i, x in enumerate(stream) if ph.update(x)), None)
    print(f"    Shewhart 3-sigma breaches on days: {hits[:6]}{'…' if len(hits) > 6 else ''}")
    print(f"    Page-Hinkley change-point flagged on day: {ph_day}")
    assert ph_day is not None and ph_day >= 60

    print("\n[3] input drift: KS distance on a shifted-mean feature")
    baseline = rng.normal(0, 1, 3000)
    drifted = rng.normal(0.35, 1, 3000)
    ks = ks_distance(baseline, drifted)
    print(f"    KS(baseline, drifted) = {ks:.3f}")

    print("\n[4] runbook output (paste into the monitoring runbook)")
    for a in runbook(hits[:2], ph_day, ks):
        print(f"    [{a.source:>13}] day={a.day:>3}  {a.detail}\n{'':21}-> {a.action}")

if __name__ == "__main__":
    main()

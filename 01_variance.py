#!/usr/bin/env python3
"""01_variance.py — Chapter 1 companion.

Implements the Box 1.1 temperature/softmax demonstration, the bootstrap
confidence-interval pattern of Sections 1.2 and 1.5, and the Figure 1.4
convergence chart. NumPy + Matplotlib only; no API key required.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(11)

# --- Box 1.1: temperature-controlled softmax ----------------------------------
def softmax_T(logits: np.ndarray, T: float) -> np.ndarray:
    z = np.asarray(logits, dtype=float) / T
    z -= z.max()
    p = np.exp(z)
    return p / p.sum()

# --- Bootstrap CI pattern ------------------------------------------------------
def bootstrap_ci(outcomes, metric, B=2000, alpha=0.05, seed=1):
    r = np.random.default_rng(seed)
    outcomes = np.asarray(outcomes)
    n = len(outcomes)
    boots = np.array([metric(outcomes[r.integers(0, n, size=n)]) for _ in range(B)])
    return (metric(outcomes),
            float(np.percentile(boots, 100 * alpha / 2)),
            float(np.percentile(boots, 100 * (1 - alpha / 2))))

def main() -> None:
    print("=" * 72)
    print("01_variance — non-determinism, sampling, and interval discipline")
    print("=" * 72)

    print("\n[1] Box 1.1: the same logits, three temperatures")
    logits = np.array([2.0, 1.0, 0.2, -1.0])
    tokens = ["approve", "refer", "decline", "escalate"]
    for T in (0.1, 1.0, 2.0):
        p = softmax_T(logits, T)
        draws = rng.choice(len(tokens), size=10_000, p=p)
        freq = np.bincount(draws, minlength=4) / 10_000
        row = ", ".join(f"{t}={f:.3f}" for t, f in zip(tokens, freq))
        print(f"    T={T:>3}: p(argmax)={p.max():.3f} | empirical: {row}")

    print("\n[2] Bootstrap CI on a 200-case accuracy sample")
    outcomes = (rng.random(200) < 0.87).astype(int)
    acc, lo, hi = bootstrap_ci(outcomes, np.mean, seed=2)
    print(f"    accuracy = {acc:.3f}, 95% CI [{lo:.3f}, {hi:.3f}] (width {hi-lo:.3f})")

    print("\n[3] Figure 1.4: CI width vs sample size (convergence chart)")
    ns = [50, 100, 200, 400, 800, 1600, 3200]
    widths = []
    for n in ns:
        o = (np.random.default_rng(n).random(n) < 0.87).astype(int)
        _, lo, hi = bootstrap_ci(o, np.mean, B=1000, seed=n)
        widths.append(hi - lo)
        print(f"    n={n:>5}: CI width = {hi-lo:.4f}")
    plt.figure(figsize=(6, 3.5))
    plt.plot(ns, widths, marker="o", color="#1F4E79")
    plt.xscale("log"); plt.xlabel("sample size n"); plt.ylabel("95% CI width")
    plt.title("Convergence of the bootstrap interval (Fig. 1.4)")
    plt.tight_layout(); plt.savefig("01_convergence.png", dpi=110)
    print("    chart written to 01_convergence.png")

    print("\n[4] Exercise stubs: non-stationary drift and tail statistics")
    drift = np.concatenate([(rng.random(500) < 0.90), (rng.random(500) < 0.80)]).astype(int)
    m1, m2 = drift[:500].mean(), drift[500:].mean()
    print(f"    regime means: first half {m1:.3f}, second half {m2:.3f} — a single pooled CI hides the break")
    lat = rng.lognormal(mean=0.3, sigma=0.8, size=5000)
    p95 = float(np.percentile(lat, 95))
    print(f"    latency: mean {lat.mean():.2f}s vs p95 {p95:.2f}s — the tail, not the mean, is the user experience")

if __name__ == "__main__":
    main()

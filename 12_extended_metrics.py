#!/usr/bin/env python3
"""12_extended_metrics.py — Chapter 12 companion.

Box 12.1's expected_calibration_error extended with bootstrap CIs and an
adaptive-bin variant; the reference-free RAG triplet (groundedness,
faithfulness, answer relevance) on a small worked corpus; heavy-tailed
latency reporting (mean vs p95); and refusal-rate tracking as a model-risk
metric. numpy only.
"""
import numpy as np

rng = np.random.default_rng(12)

# --- Box 12.1: ECE in twelve lines, plus variants -------------------------------
def expected_calibration_error(probs, correct, n_bins=10):
    probs, correct = np.asarray(probs, float), np.asarray(correct, float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece, n = 0.0, len(probs)
    for b in range(n_bins):
        mask = (probs >= bins[b]) & (probs < bins[b + 1])
        if b == n_bins - 1:
            mask |= probs == 1.0
        if mask.sum() > 0:
            ece += mask.sum() / n * abs(correct[mask].mean() - probs[mask].mean())
    return float(ece)

def adaptive_ece(probs, correct, n_bins=10):
    """Equal-count (quantile) bins rather than equal-width."""
    probs, correct = np.asarray(probs, float), np.asarray(correct, float)
    order = np.argsort(probs)
    ece, n = 0.0, len(probs)
    for chunk in np.array_split(order, n_bins):
        if len(chunk):
            ece += len(chunk) / n * abs(correct[chunk].mean() - probs[chunk].mean())
    return float(ece)

def bootstrap_ci(x, metric, B=1000, alpha=0.05, seed=0):
    r = np.random.default_rng(seed); x = np.arange(len(x[0])) if isinstance(x, tuple) else np.asarray(x)
    raise NotImplementedError  # replaced below with paired version

def paired_bootstrap(probs, correct, metric, B=1000, alpha=0.05, seed=5):
    r = np.random.default_rng(seed)
    n = len(probs)
    vals = []
    for _ in range(B):
        idx = r.integers(0, n, size=n)
        vals.append(metric(probs[idx], correct[idx]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))

# --- Reference-free RAG triplet ---------------------------------------------------
def _claims(text): return [c.strip() for c in text.split(".") if c.strip()]

def _supported(claim, context):
    """A claim is supported if most of its content words (len > 4) appear in
    the context, matching on 4-character prefixes to absorb inflection."""
    ctx = context.lower()
    content = [w.strip(",.") for w in claim.lower().split() if len(w.strip(",.")) > 4]
    if not content:
        return any(w in ctx for w in claim.lower().split())
    hits = sum(1 for w in content if w[:4] in ctx)
    return hits > len(content) / 2

def groundedness(answer, context):
    cs = _claims(answer)
    return sum(_supported(c, context) for c in cs) / len(cs)

def faithfulness(answer, context):
    contradictions = sum(1 for c in _claims(answer) if "not " in c.lower() and c.lower().replace("not ", "") in context.lower())
    return 1.0 - contradictions / max(1, len(_claims(answer)))

def answer_relevance(answer, question):
    qw = set(question.lower().split())
    aw = set(answer.lower().split())
    return len(qw & aw) / len(qw)

def main() -> None:
    print("=" * 72)
    print("12_extended_metrics — calibration, the RAG triplet, tails, refusals")
    print("=" * 72)

    print("\n[1] ECE with bootstrap CI, equal-width vs adaptive bins (n=2,000)")
    probs = np.clip(rng.beta(6, 2, 2000), 0, 1)
    correct = (rng.random(2000) < probs * 0.92).astype(float)   # mildly over-confident system
    ece = expected_calibration_error(probs, correct)
    lo, hi = paired_bootstrap(probs, correct, expected_calibration_error)
    aece = adaptive_ece(probs, correct)
    print(f"    ECE = {ece:.4f}  95% CI [{lo:.4f}, {hi:.4f}]   adaptive-bin ECE = {aece:.4f}")

    print("\n[2] reference-free RAG triplet on the worked example")
    context = ("Andy Bakery LIMITED requests a facility of GBP 88,000 over 36 months. "
               "The bakery reported revenue of GBP 412,000 and DSCR of 1.6x.")
    question = "What facility is requested and what is the DSCR?"
    answer = "The facility requested is GBP 88,000 over 36 months. DSCR is 1.6x. The bakery operates in Leeds."
    g, f, ar = groundedness(answer, context), faithfulness(answer, context), answer_relevance(answer, question)
    print(f"    groundedness = {g:.2f} (the Leeds claim is unsupported)")
    print(f"    faithfulness = {f:.2f}   answer relevance = {ar:.2f}")
    assert g < 1.0

    print("\n[3] heavy-tailed latency: the mean is not the user experience")
    lat = rng.lognormal(0.4, 0.9, 10_000)
    print(f"    mean = {lat.mean():.2f}s   p50 = {np.percentile(lat,50):.2f}s   "
          f"p95 = {np.percentile(lat,95):.2f}s   p99 = {np.percentile(lat,99):.2f}s")

    print("\n[4] refusal rate as a model-risk metric (weekly, with a vendor update at week 8)")
    weeks = np.concatenate([rng.normal(0.031, 0.003, 8), rng.normal(0.074, 0.004, 4)])
    for i, w in enumerate(weeks, 1):
        flag = "  <- step change: vendor safety-filter tightening?" if i == 9 else ""
        print(f"    week {i:>2}: refusal rate {w:.3f}{flag}")
    print("    An unexpectedly high refusal rate is a monitoring alert, not a safety comfort.")

if __name__ == "__main__":
    main()

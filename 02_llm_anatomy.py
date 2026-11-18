#!/usr/bin/env python3
"""02_llm_anatomy.py — Chapter 2 companion.

Toy greedy longest-match BPE-style tokeniser; temperature softmax with
empirical sampling at T=0.1/1.0/2.0; top-k and top-p truncation with
empirical frequency comparison; parameter counting for three reference
scales. numpy only; no vendor API access.
"""
import numpy as np

rng = np.random.default_rng(22)

# --- Toy tokeniser -------------------------------------------------------------
VOCAB = ["the", " applicant", " has", " 11", " 1", "1", " CCJ", "s", " from", " 20", "20", "1", "9",
         " ", "a", "p", "l", "i", "c", "n", "t", "h", "s", "C", "J", "f", "r", "o", "m", "0", "2", "9", "e"]

def tokenise(text: str, vocab=None):
    vocab = sorted(set(vocab or VOCAB), key=len, reverse=True)  # greedy longest match
    out, i = [], 0
    while i < len(text):
        for v in vocab:
            if text.startswith(v, i):
                out.append(v); i += len(v); break
        else:
            out.append(text[i]); i += 1
    ids = {v: k for k, v in enumerate(sorted(set(out) | set(vocab)))}
    return out, [ids[t] for t in out]

# --- Sampling machinery ---------------------------------------------------------
def softmax_T(logits, T):
    z = np.asarray(logits, float) / T; z -= z.max()
    p = np.exp(z); return p / p.sum()

def top_k(p, k):
    q = np.zeros_like(p); idx = np.argsort(p)[::-1][:k]
    q[idx] = p[idx]; return q / q.sum()

def top_p(p, thresh):
    order = np.argsort(p)[::-1]
    cum = np.cumsum(p[order])
    keep = order[: int(np.searchsorted(cum, thresh) + 1)]
    q = np.zeros_like(p); q[keep] = p[keep]; return q / q.sum()

# --- Parameter counting ----------------------------------------------------------
def param_count(n_layers, d_model, n_vocab, d_ff=None):
    d_ff = d_ff or 4 * d_model
    per_layer = 4 * d_model * d_model + 2 * d_model * d_ff  # attn (QKVO) + MLP
    return n_vocab * d_model + n_layers * per_layer

def main() -> None:
    print("=" * 72)
    print("02_llm_anatomy — every primitive, from first principles")
    print("=" * 72)

    print("\n[1] Tokenisation: 'The applicant has 11 CCJs from 2019'")
    toks, ids = tokenise("the applicant has 11 CCJs from 2019")
    print(f"    tokens ({len(toks)}): {toks}")
    print(f"    ids: {ids}")
    print("    NOTE: '11' and '2019' fragment — numerals are not atomic to the model.")

    print("\n[2] Temperature: empirical frequencies over 20,000 draws")
    logits = np.array([3.0, 2.2, 1.0, 0.0, -1.0])
    for T in (0.1, 1.0, 2.0):
        p = softmax_T(logits, T)
        draws = rng.choice(5, size=20_000, p=p)
        f = np.bincount(draws, minlength=5) / 20_000
        print(f"    T={T:>3}: p={np.round(p,3)} empirical={np.round(f,3)}")

    print("\n[3] Truncation: top-k=2 vs top-p=0.9 on the same distribution")
    p = softmax_T(logits, 1.0)
    for name, q in (("top-k(2)", top_k(p, 2)), ("top-p(0.9)", top_p(p, 0.9))):
        draws = rng.choice(5, size=20_000, p=q)
        f = np.bincount(draws, minlength=5) / 20_000
        print(f"    {name:>10}: support={int((q>0).sum())} empirical={np.round(f,3)}")

    print("\n[4] Parameter counting for three reference scales")
    for name, L, d, V in (("GPT-2-small", 12, 768, 50257),
                          ("Llama-3-8B", 32, 4096, 128256),
                          ("GPT-3-175B", 96, 12288, 50257)):
        n = param_count(L, d, V)
        print(f"    {name:>12}: layers={L:>2} d_model={d:>5} vocab={V:>6} -> ~{n/1e9:.1f}B params")

if __name__ == "__main__":
    main()

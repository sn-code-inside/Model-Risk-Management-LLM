#!/usr/bin/env python3
"""21_information_barrier_check.py — Chapter 21 companion.

Side enum (public/private); side-tagged Document corpus; two retrieval
implementations (naive unified index vs side-aware); an eight-query
adversarial probe battery; probe harness producing the cross-side leak rate.
Reproduces the chapter's result: naive leaks on five of eight probes,
side-aware on zero. Standard library only; production uses vector retrieval
but the boundary-at-the-retrieval-function pattern transfers directly.
"""
from dataclasses import dataclass
from enum import Enum

class Side(Enum):
    PUBLIC = "public"
    PRIVATE = "private"

@dataclass
class Document:
    doc_id: str
    side: Side
    text: str

CORPUS = [
    Document("RES-001", Side.PUBLIC, "Equity research: HighStreet Retail plc initiation, sector overview, margin outlook"),
    Document("RES-002", Side.PUBLIC, "Sector note: UK grocery consolidation themes and valuation multiples"),
    Document("RES-003", Side.PUBLIC, "Macro note: rates path and consumer discretionary spending"),
    Document("MA-101", Side.PRIVATE, "Project FALCON: mandate to advise BidCo on acquisition of HighStreet Retail plc, offer premium 32%"),
    Document("MA-102", Side.PRIVATE, "Project FALCON synergies model and financing structure, bridge facility terms"),
    Document("MA-103", Side.PRIVATE, "Draft announcement timetable for HighStreet Retail plc take-private"),
]

def _score(query: str, doc: Document) -> int:
    q = set(query.lower().split())
    return len(q & set(doc.text.lower().split()))

def naive_retrieve(query, corpus=CORPUS, k=2):
    return sorted(corpus, key=lambda d: -_score(query, d))[:k]

def side_aware_retrieve(query, caller_side: Side, corpus=CORPUS, k=2):
    allowed = [d for d in corpus if d.side == caller_side]
    return sorted(allowed, key=lambda d: -_score(query, d))[:k]

PROBES = [
    "any deal activity around HighStreet Retail plc",
    "acquisition premium HighStreet Retail",
    "Project FALCON details",
    "financing structure for the HighStreet take-private",
    "announcement timetable HighStreet Retail plc",
    "UK grocery valuation multiples",
    "rates path consumer spending outlook",
    "sector overview margin outlook grocery consolidation",
]

def run_probes(retriever, label):
    leaks = 0
    detail = []
    for q in PROBES:
        hits = retriever(q)
        leaked = [d.doc_id for d in hits if d.side == Side.PRIVATE and _score(q, d) > 0]
        leaks += bool(leaked)
        detail.append((q, leaked))
    return leaks, detail

def main() -> None:
    print("=" * 72)
    print("21_information_barrier_check — the boundary lives in the retrieval function")
    print("=" * 72)

    print("\n[1] naive unified index (public-side research analyst issuing the probes)")
    n_leaks, detail = run_probes(lambda q: naive_retrieve(q), "naive")
    for q, leaked in detail:
        print(f"    {'LEAK ' + str(leaked) if leaked else 'clean':<28} <- \"{q}\"")
    print(f"    cross-side leak rate: {n_leaks}/8")

    print("\n[2] side-aware retrieval (same probes, caller side enforced)")
    s_leaks, detail = run_probes(lambda q: side_aware_retrieve(q, Side.PUBLIC), "side-aware")
    for q, leaked in detail:
        print(f"    {'LEAK ' + str(leaked) if leaked else 'clean':<28} <- \"{q}\"")
    print(f"    cross-side leak rate: {s_leaks}/8")

    assert n_leaks == 5 and s_leaks == 0, (n_leaks, s_leaks)
    print("\nHeadline metric for the validation file: cross-side leak rate 5/8 (naive) vs 0/8 (side-aware).")
    print("MAR/MiFID relevance follows from the leak, not from the retrieval technology.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""00_book_conventions.py — Chapter 0 companion.

Verifies the book's conventions in runnable Python: the IEEE numbered
citation format, the eight-class artefact taxonomy (Ch 5), the
three-attachment-point evidence structure (Ch 8), and the regulatory
citation idiom. Standard library only.
"""
from dataclasses import dataclass, field
from enum import Enum

# --- IEEE numbered citations -------------------------------------------------
BIBLIOGRAPHY = {
    2: 'Fed/OCC/FDIC, "SR 26-2: Revised Guidance on Model Risk Management," Apr. 17, 2026.',
    5: 'PRA, "SS1/23: Model Risk Management Principles for Banks," May 2023.',
    6: 'EP and Council, "Regulation (EU) 2024/1689 (AI Act)," OJ L, 2024.',
}

def cite(n: int) -> str:
    assert n in BIBLIOGRAPHY, f"dangling citation [{n}]"
    return f"[{n}]"

# --- Eight-class artefact taxonomy (Ch 5) ------------------------------------
class ArtefactClass(Enum):
    FOUNDATION_MODEL = "foundation_model"
    APPLICATION = "application"
    PROMPT_TEMPLATE = "prompt_template"
    EMBEDDING_MODEL = "embedding_model"
    RETRIEVAL_INDEX = "retrieval_index"
    OUTPUT_VALIDATOR = "output_validator"
    AGENT_TOOL = "agent_tool"
    AGENT_MEMORY = "agent_memory"

@dataclass
class Artefact:
    name: str
    cls: ArtefactClass
    version: str
    vendor: str = "firm"
    pinned: bool = True

# --- Three attachment points (Ch 8) -------------------------------------------
class AttachmentPoint(Enum):
    PER_ARTEFACT = "per-artefact"
    COMPOSITION = "composition"
    ORCHESTRATION = "orchestration"

@dataclass
class Evidence:
    metric: str
    point: AttachmentPoint
    value: float
    threshold: float
    direction: str = ">="  # ">=" or "<="

    @property
    def passed(self) -> bool:
        return self.value >= self.threshold if self.direction == ">=" else self.value <= self.threshold

def main() -> None:
    print("=" * 72)
    print("00_book_conventions — conventions check")
    print("=" * 72)

    print("\n[1] IEEE citation format")
    print(f"    The US MRM baseline is SR 26-2 {cite(2)}; the UK baseline is SS1/23 {cite(5)};")
    print(f"    the EU regime is the AI Act {cite(6)}.")

    print("\n[2] Artefact taxonomy: eight classes")
    assert len(ArtefactClass) == 8
    for c in ArtefactClass:
        print(f"    - {c.value}")

    print("\n[3] Attachment-point structure: worked example (six evidence items)")
    ev = [
        Evidence("groundedness", AttachmentPoint.PER_ARTEFACT, 0.96, 0.95),
        Evidence("retrieval_recall@5", AttachmentPoint.PER_ARTEFACT, 0.91, 0.90),
        Evidence("schema_valid_rate", AttachmentPoint.PER_ARTEFACT, 1.00, 0.999),
        Evidence("task_accuracy", AttachmentPoint.COMPOSITION, 0.89, 0.85),
        Evidence("vulnerable_segment_accuracy", AttachmentPoint.COMPOSITION, 0.86, 0.85),
        Evidence("p95_latency_s", AttachmentPoint.ORCHESTRATION, 4.2, 6.0, "<="),
    ]
    by_point = {}
    for e in ev:
        by_point.setdefault(e.point, []).append(e)
    for p in AttachmentPoint:
        items = by_point.get(p, [])
        print(f"    {p.value:>14}: {len(items)} item(s), all pass = {all(i.passed for i in items)}")
    assert all(e.passed for e in ev)

    print("\n[4] Regulatory citation idiom")
    print("    'SR 26-2 § IV; SS1/23 Principle 4; EU AI Act Art. 14' — instrument, division, date checked at use.")

    print("\nAll conventions verified. Ready for Chapter 1.")

if __name__ == "__main__":
    main()

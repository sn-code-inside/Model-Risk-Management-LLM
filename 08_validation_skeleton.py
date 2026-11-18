#!/usr/bin/env python3
"""08_validation_skeleton.py — Chapter 8 companion.

Evidence dataclass with pass/fail logic; AttachmentPoint enum; ValidationFile
with by-point accessors and a completeness check; SignOff with the
fingerprint-bound is_valid_for() method; worked example on the credit-memo
summariser (seven evidence items across three points), then the
fingerprint-drift demonstration. Standard library only.
"""
import hashlib
from dataclasses import dataclass, field
from datetime import date
from enum import Enum

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
    direction: str = ">="
    n: int = 0

    @property
    def passed(self) -> bool:
        return self.value >= self.threshold if self.direction == ">=" else self.value <= self.threshold

@dataclass
class ValidationFile:
    system: str
    evidence: list = field(default_factory=list)

    def by_point(self, p): return [e for e in self.evidence if e.point == p]

    def complete(self) -> bool:
        return all(len(self.by_point(p)) > 0 for p in AttachmentPoint)

    def all_pass(self) -> bool:
        return all(e.passed for e in self.evidence)

def system_fingerprint(config: dict) -> str:
    blob = "|".join(f"{k}={config[k]}" for k in sorted(config))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]

@dataclass
class SignOff:
    validator_name: str
    validator_role: str
    signed: date
    stated_use: str
    fingerprint: str

    def is_valid_for(self, current_config: dict, use: str) -> bool:
        return self.fingerprint == system_fingerprint(current_config) and use == self.stated_use

def main() -> None:
    print("=" * 72)
    print("08_validation_skeleton — evidence, attachment points, and the sign-off contract")
    print("=" * 72)

    config = {"foundation_model": "gpt-x@2026-05-01", "prompt_fp": "a41c9f2e",
              "embedding_model": "embed-large@3.1", "sampling": "T=0.2",
              "corpus_snapshot": "2026-06-30"}
    vf = ValidationFile("credit-memo summariser", [
        Evidence("groundedness", AttachmentPoint.PER_ARTEFACT, 0.962, 0.95, n=400),
        Evidence("retrieval_recall@5", AttachmentPoint.PER_ARTEFACT, 0.914, 0.90, n=400),
        Evidence("schema_valid_rate", AttachmentPoint.PER_ARTEFACT, 0.9995, 0.999, n=2000),
        Evidence("task_accuracy", AttachmentPoint.COMPOSITION, 0.891, 0.85, n=400),
        Evidence("vulnerable_segment_accuracy", AttachmentPoint.COMPOSITION, 0.862, 0.85, n=120),
        Evidence("fallback_correct_rate", AttachmentPoint.ORCHESTRATION, 0.99, 0.98, n=200),
        Evidence("p95_latency_s", AttachmentPoint.ORCHESTRATION, 4.2, 6.0, "<=", n=2000),
    ])

    print(f"\n[1] {vf.system}: {len(vf.evidence)} evidence items")
    for p in AttachmentPoint:
        for e in vf.by_point(p):
            print(f"    [{p.value:>13}] {e.metric:<28} {e.value:>7} {e.direction} {e.threshold:<6} "
                  f"n={e.n:<5} {'PASS' if e.passed else 'FAIL'}")
    print(f"    completeness: {vf.complete()}   all pass: {vf.all_pass()}")
    assert vf.complete() and vf.all_pass()

    print("\n[2] sign-off, fingerprint-bound")
    so = SignOff("A. Levi", "Head of Model Risk (2LoD)", date(2026, 7, 1),
                 "credit-memo summarisation, decision-support", system_fingerprint(config))
    print(f"    fingerprint {so.fingerprint} — valid for current config: {so.is_valid_for(config, so.stated_use)}")
    assert so.is_valid_for(config, so.stated_use)

    print("\n[3] fingerprint drift: a single character changes in the configuration")
    drifted = dict(config, foundation_model="gpt-x@2026-05-02")   # silent vendor update
    print(f"    valid after vendor update: {so.is_valid_for(drifted, so.stated_use)}")
    assert not so.is_valid_for(drifted, so.stated_use)
    print("    the sign-off invalidates mechanically; the deployment pipeline can refuse the drifted config.")
    print("    (Ch 9: this is a detective control — pair it with version pinning and vendor notice terms.)")

if __name__ == "__main__":
    main()

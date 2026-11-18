#!/usr/bin/env python3
"""18_consumer_duty_validator.py — Chapter 18 companion.

EvidenceRequirement encoding the ten retail requirements across the four
FG22/5 outcomes; EvidenceItem and a stripped-down RetailValidationFile;
ConsumerDutyOverlay.assess() producing per-outcome OutcomeReports with
named missing/failing evidence and a mechanical overall pass/fail. Runs the
customer-correspondence assistant twice: v2.3 passes; v2.4 fails consumer
understanding and consumer support and is blocked. Standard library only.
"""
from dataclasses import dataclass, field

OUTCOMES = ["Products and services", "Price and value", "Consumer understanding", "Consumer support"]

@dataclass
class EvidenceRequirement:
    req_id: str
    outcome: str
    metric: str
    threshold: float
    direction: str = ">="

REQUIREMENTS = [
    EvidenceRequirement("PS-1", "Products and services", "target_market_appropriateness", 0.90),
    EvidenceRequirement("PS-2", "Products and services", "distribution_scope_conformance", 0.99),
    EvidenceRequirement("PV-1", "Price and value", "fee_disclosure_accuracy", 0.995),
    EvidenceRequirement("PV-2", "Price and value", "value_assessment_current", 1.0),
    EvidenceRequirement("CU-1", "Consumer understanding", "reading_age_grade_max", 9.0, "<="),
    EvidenceRequirement("CU-2", "Consumer understanding", "comprehension_test_pass_rate", 0.80),
    EvidenceRequirement("CU-3", "Consumer understanding", "key_terms_presence_rate", 0.99),
    EvidenceRequirement("CS-1", "Consumer support", "vulnerable_segment_accuracy", 0.85),
    EvidenceRequirement("CS-2", "Consumer support", "escalation_route_offered_rate", 0.99),
    EvidenceRequirement("CS-3", "Consumer support", "unresolved_query_followup_rate", 0.95),
]

@dataclass
class EvidenceItem:
    metric: str
    value: float
    n: int

@dataclass
class RetailValidationFile:
    system: str
    version: str
    items: dict  # metric -> EvidenceItem

@dataclass
class OutcomeReport:
    outcome: str
    passed: bool
    missing: list
    failing: list

class ConsumerDutyOverlay:
    def __init__(self, requirements=REQUIREMENTS):
        self.requirements = requirements

    def assess(self, vf: RetailValidationFile):
        reports = []
        for outcome in OUTCOMES:
            reqs = [r for r in self.requirements if r.outcome == outcome]
            missing, failing = [], []
            for r in reqs:
                item = vf.items.get(r.metric)
                if item is None:
                    missing.append(r.req_id + ":" + r.metric)
                else:
                    ok = item.value >= r.threshold if r.direction == ">=" else item.value <= r.threshold
                    if not ok:
                        failing.append(f"{r.req_id}:{r.metric}={item.value} vs {r.direction}{r.threshold}")
            reports.append(OutcomeReport(outcome, not missing and not failing, missing, failing))
        return reports, all(r.passed for r in reports)

def make_file(version, overrides=None, drop=()):
    base = {"target_market_appropriateness": (0.93, 300), "distribution_scope_conformance": (0.998, 2000),
            "fee_disclosure_accuracy": (0.998, 1000), "value_assessment_current": (1.0, 1),
            "reading_age_grade_max": (8.2, 400), "comprehension_test_pass_rate": (0.84, 250),
            "key_terms_presence_rate": (0.995, 1000), "vulnerable_segment_accuracy": (0.87, 150),
            "escalation_route_offered_rate": (0.997, 1000), "unresolved_query_followup_rate": (0.97, 400)}
    base.update(overrides or {})
    for d in drop:
        base.pop(d, None)
    return RetailValidationFile("customer-correspondence assistant", version,
                                {m: EvidenceItem(m, v, n) for m, (v, n) in base.items()})

def show(reports, overall, version):
    print(f"\n    version {version}:")
    for r in reports:
        line = f"      {r.outcome:<24} {'PASS' if r.passed else 'FAIL'}"
        if r.missing: line += f"  missing: {r.missing}"
        if r.failing: line += f"  failing: {r.failing}"
        print(line)
    print(f"      OVERALL: {'PASS — release may proceed' if overall else 'BLOCKED — release gate holds'}")

def main() -> None:
    print("=" * 72)
    print("18_consumer_duty_validator — the four-outcomes overlay as a release gate")
    print("=" * 72)
    overlay = ConsumerDutyOverlay()

    v23 = make_file("2.3")
    r23, ok23 = overlay.assess(v23)
    show(r23, ok23, "2.3")
    assert ok23

    v24 = make_file("2.4",
                    overrides={"vulnerable_segment_accuracy": (0.79, 150)},
                    drop=("comprehension_test_pass_rate",))
    r24, ok24 = overlay.assess(v24)
    show(r24, ok24, "2.4 (candidate)")
    assert not ok24
    failed = {r.outcome for r in r24 if not r.passed}
    assert failed == {"Consumer understanding", "Consumer support"}, failed
    print("\nThe overlay names the evidence, not just the verdict — that is what 2LoD review needs.")

if __name__ == "__main__":
    main()

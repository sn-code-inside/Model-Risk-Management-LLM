#!/usr/bin/env python3
"""22_firm_self_assessment.py — Chapter 22 companion.

AssessmentItem capturing the twenty-one questions keyed to the book's
chapters; AssessmentResponse/FirmAssessment; the Box 22.1 80%-rule phase
progression; current_phase(); gaps() surfacing unanswered items as the
priority list. Worked example: a mid-sized UK bank scoring 5/7, 5/7, 1/4 —
correctly classified as still in Phase 1 with seven specific gaps.
Standard library only.
"""
from dataclasses import dataclass, field

@dataclass
class AssessmentItem:
    item_id: str
    phase: int
    chapter: str
    question: str

ITEMS = [
    # Phase 1 — Foundations (7)
    AssessmentItem("P1-1", 1, "Ch 5-6", "Is every LLM application decomposed into the eight artefact classes and inventoried?"),
    AssessmentItem("P1-2", 1, "Ch 3", "Does each inventory entry carry a per-use-case regulatory classification?"),
    AssessmentItem("P1-3", 1, "Ch 3", "Is a materiality tier (inherent risk x exposure x purpose) assigned and documented?"),
    AssessmentItem("P1-4", 1, "Ch 7", "Are prompt templates versioned, fingerprinted, and changed through review?"),
    AssessmentItem("P1-5", 1, "Ch 9", "Is there a vendor inventory with the four-provision LLM contractual minimum?"),
    AssessmentItem("P1-6", 1, "Ch 8", "Is validation sign-off fingerprint-bound so configuration change re-opens it?"),
    AssessmentItem("P1-7", 1, "Ch 6", "Are unpinned or un-versionable artefacts surfaced as open findings?"),
    # Phase 2 — Validation discipline (7)
    AssessmentItem("P2-1", 2, "Ch 10", "Are test sets stratified backwards from per-segment interval targets?"),
    AssessmentItem("P2-2", 2, "Ch 11", "Do headline metrics carry bootstrap confidence intervals?"),
    AssessmentItem("P2-3", 2, "Ch 11", "Are LLM judges calibrated against human ratings (weighted kappa) before use?"),
    AssessmentItem("P2-4", 2, "Ch 12", "Is a metric portfolio (beyond accuracy) matched to the architecture?"),
    AssessmentItem("P2-5", 2, "Ch 13", "Is fairness evidence produced per protected-group with explicit criteria choices?"),
    AssessmentItem("P2-6", 2, "Ch 15", "Is red-teaming run as a standing cycle with severity-by-ease dispositions?"),
    AssessmentItem("P2-7", 2, "Ch 11", "Is a regression baseline frozen and re-run on every artefact change?"),
    # Phase 3 — Operations (4)
    AssessmentItem("P3-1", 3, "Ch 16", "Is production sampled, charted, and change-point monitored per the runbook?"),
    AssessmentItem("P3-2", 3, "Ch 17", "Do incidents follow the severity taxonomy with the notification default applied?"),
    AssessmentItem("P3-3", 3, "Ch 14", "Are agent tools gated by the capability-x-reversibility approval matrix?"),
    AssessmentItem("P3-4", 3, "Ch 22", "Is the framework reviewed against the revision-horizon catalogue twice a year?"),
    # Cross-cutting (3) — informational, not phase-scored
    AssessmentItem("X-1", 0, "Ch 18-21", "Are sector overlays (Consumer Duty, deal-type, vulnerability, barriers) applied?"),
    AssessmentItem("X-2", 0, "Ch 2", "Can the validation team explain tokenisation, sampling, and temperature to 2LoD?"),
    AssessmentItem("X-3", 0, "Ch 22", "Is there a named senior manager accountable for the MRM-for-LLMs framework?"),
]

@dataclass
class AssessmentResponse:
    item_id: str
    answer: bool
    note: str = ""

@dataclass
class FirmAssessment:
    firm: str
    responses: dict  # item_id -> AssessmentResponse

    def phase_score(self, phase: int):
        items = [i for i in ITEMS if i.phase == phase]
        yes = sum(1 for i in items if self.responses.get(i.item_id, AssessmentResponse(i.item_id, False)).answer)
        return yes, len(items)

    def current_phase(self, rule=0.8):
        """Box 22.1: a phase counts as complete at >=80% yes; the firm sits in
        the first incomplete phase."""
        for phase in (1, 2, 3):
            yes, n = self.phase_score(phase)
            if yes / n < rule:
                return phase
        return 4  # steady state

    def gaps(self):
        out = []
        for i in ITEMS:
            if i.phase == 0:
                continue
            r = self.responses.get(i.item_id)
            if not (r and r.answer):
                out.append(i)
        return out

def main() -> None:
    print("=" * 72)
    print("22_firm_self_assessment — twenty-one questions, one board conversation")
    print("=" * 72)
    assert len(ITEMS) == 21

    answers = {  # mid-sized UK bank
        "P1-1": True, "P1-2": True, "P1-3": True, "P1-4": True, "P1-5": False,
        "P1-6": True, "P1-7": False,
        "P2-1": True, "P2-2": True, "P2-3": False, "P2-4": True, "P2-5": True,
        "P2-6": False, "P2-7": True,
        "P3-1": True, "P3-2": False, "P3-3": False, "P3-4": False,
        "X-1": False, "X-2": True, "X-3": True,
    }
    fa = FirmAssessment("Mid-sized UK bank",
                        {k: AssessmentResponse(k, v) for k, v in answers.items()})

    print("\n[1] phase scores (Box 22.1: 80% rule)")
    for p, label in ((1, "Foundations"), (2, "Validation discipline"), (3, "Operations")):
        yes, n = fa.phase_score(p)
        print(f"    Phase {p} {label:<22}: {yes}/{n}  ({yes/n:.0%})")
    s1, s2, s3 = fa.phase_score(1), fa.phase_score(2), fa.phase_score(3)
    assert (s1, s2, s3) == ((5, 7), (5, 7), (1, 4)), (s1, s2, s3)

    phase = fa.current_phase()
    print(f"\n[2] classification: the firm is still in Phase {phase}")
    assert phase == 1
    print("    71% on Phase 1 does not clear the 80% bar — foundations first, whatever Phase 2 looks like.")

    gaps = fa.gaps()
    print(f"\n[3] gap report ({len(gaps)} items — the operational priority list)")
    assert len(gaps) == 7, len(gaps)
    for g in gaps:
        print(f"    [{g.item_id}] ({g.chapter}) {g.question}")
    print("\nProduction deployments join this to the Ch 6 inventory so gaps name applications, not categories.")

if __name__ == "__main__":
    main()

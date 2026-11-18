#!/usr/bin/env python3
"""14_agent_governance.py — Chapter 14 companion.

Capability, Reversibility, ApprovalMode enums; Tool with required_approval;
control-point functions C1–C4; AgentAction/ActionRecord for audit; worked
example on the eleven-tool KYC catalogue: READ auto-approves, WRITE
auto-approves-with-log, decision.approve requires a human. Standard library
only.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

class Capability(Enum):
    READ = "read"
    WRITE = "write"
    DECIDE = "decide"

class Reversibility(Enum):
    REVERSIBLE = "reversible"
    COSTLY = "costly"
    IRREVERSIBLE = "irreversible"

class ApprovalMode(Enum):
    AUTO = "auto-approve"
    AUTO_LOG = "auto-approve-with-log"
    HUMAN = "human-approval-required"

@dataclass
class Tool:
    name: str
    capability: Capability
    reversibility: Reversibility

    @property
    def required_approval(self) -> ApprovalMode:
        if self.capability == Capability.READ:
            return ApprovalMode.AUTO
        if self.capability == Capability.WRITE and self.reversibility != Reversibility.IRREVERSIBLE:
            return ApprovalMode.AUTO_LOG
        return ApprovalMode.HUMAN

@dataclass
class AgentAction:
    tool: str
    args: dict

@dataclass
class ActionRecord:
    action: AgentAction
    mode: ApprovalMode
    approved: bool
    approver: str
    ts: str

# --- Control points ---------------------------------------------------------------
def C1_catalogue_gate(tool_name, catalogue):
    return tool_name in {t.name for t in catalogue}

def C2_input_guard(action: AgentAction):
    banned = ("DROP ", "sudo ", "IGNORE ALL")
    return not any(b.lower() in str(action.args).lower() for b in banned)

def C3_approval_gate(action, catalogue, human_decision=None):
    tool = next(t for t in catalogue if t.name == action.tool)
    mode = tool.required_approval
    if mode == ApprovalMode.HUMAN:
        approved = bool(human_decision)
        approver = "named-approver" if human_decision is not None else "pending"
    else:
        approved, approver = True, "system"
    return ActionRecord(action, mode, approved, approver,
                        datetime(2026, 7, 14, tzinfo=timezone.utc).isoformat())

def C4_audit(records):
    return [{"tool": r.action.tool, "mode": r.mode.value, "approved": r.approved,
             "approver": r.approver, "ts": r.ts} for r in records]

KYC_CATALOGUE = [
    Tool("registry.company_profile", Capability.READ, Reversibility.REVERSIBLE),
    Tool("registry.officers", Capability.READ, Reversibility.REVERSIBLE),
    Tool("registry.psc", Capability.READ, Reversibility.REVERSIBLE),
    Tool("sanctions.screen", Capability.READ, Reversibility.REVERSIBLE),
    Tool("adverse_media.search", Capability.READ, Reversibility.REVERSIBLE),
    Tool("cifas.check", Capability.READ, Reversibility.REVERSIBLE),
    Tool("case.update_notes", Capability.WRITE, Reversibility.REVERSIBLE),
    Tool("case.attach_document", Capability.WRITE, Reversibility.REVERSIBLE),
    Tool("case.set_risk_rating", Capability.WRITE, Reversibility.COSTLY),
    Tool("customer.request_documents", Capability.WRITE, Reversibility.COSTLY),
    Tool("decision.approve", Capability.DECIDE, Reversibility.IRREVERSIBLE),
]

def main() -> None:
    print("=" * 72)
    print("14_agent_governance — capability x reversibility -> approval mode")
    print("=" * 72)
    assert len(KYC_CATALOGUE) == 11

    print("\n[1] the eleven-tool KYC catalogue and its approval modes")
    for t in KYC_CATALOGUE:
        print(f"    {t.name:<28} {t.capability.value:>6} / {t.reversibility.value:<12} -> {t.required_approval.value}")

    print("\n[2] a KYC run through C1-C4")
    actions = [AgentAction("registry.company_profile", {"company": "Andy Bakery LIMITED"}),
               AgentAction("sanctions.screen", {"name": "A. Baker"}),
               AgentAction("case.update_notes", {"note": "PSC verified; no sanctions hits"}),
               AgentAction("case.set_risk_rating", {"rating": "LOW"}),
               AgentAction("decision.approve", {"case": "KYC-88231"})]
    records = []
    for a in actions:
        assert C1_catalogue_gate(a.tool, KYC_CATALOGUE), f"C1: {a.tool} not in catalogue"
        assert C2_input_guard(a), f"C2: blocked args for {a.tool}"
        rec = C3_approval_gate(a, KYC_CATALOGUE,
                               human_decision=True if a.tool == "decision.approve" else None)
        records.append(rec)
        print(f"    {a.tool:<28} -> {rec.mode.value:<26} approved={rec.approved} by {rec.approver}")
    modes = [r.mode for r in records]
    assert modes[0] == ApprovalMode.AUTO and modes[2] == ApprovalMode.AUTO_LOG and modes[-1] == ApprovalMode.HUMAN

    print("\n[3] C4 audit trail (paste into the case file)")
    for row in C4_audit(records):
        print(f"    {row}")
    print("\nOff-catalogue and injected actions never reach C3; the human sits exactly where irreversibility sits.")

if __name__ == "__main__":
    main()

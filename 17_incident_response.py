#!/usr/bin/env python3
"""17_incident_response.py — Chapter 17 companion.

Severity enums and classify_severity; IncidentTicket with timeline tracking
and requires_supervisory_notification; Action dataclass; PostMortem with a
render() producing the four-section template. Walks IR-2026-0042 end to end.
Standard library only. The notification rule is the chapter's deliberately
mechanical default, not the legal test.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class Severity(Enum):
    SEV1 = "SEV-1"
    SEV2 = "SEV-2"
    SEV3 = "SEV-3"

def classify_severity(customers_affected: int, operational_severity: str, duration_hours: float) -> Severity:
    if operational_severity == "critical" and customers_affected > 500:
        return Severity.SEV1
    if operational_severity in ("critical", "major") and (customers_affected > 50 or duration_hours > 4):
        return Severity.SEV2
    return Severity.SEV3

@dataclass
class Action:
    owner: str
    description: str
    due: str
    done: bool = False

@dataclass
class IncidentTicket:
    incident_id: str
    system: str
    severity: Severity = Severity.SEV3
    customers_affected: int = 0
    duration_hours: float = 0.0
    timeline: list = field(default_factory=list)
    actions: list = field(default_factory=list)

    def log(self, ts: str, event: str):
        self.timeline.append((ts, event))

    def requires_supervisory_notification(self) -> bool:
        """Mechanical default (SUP 15.3 presumption), not the legal test:
        SEV-1 presumed notifiable; SEV-2 presumed notifiable if >500 customers
        AND >4 hours; SEV-3 presumed not notifiable."""
        if self.severity == Severity.SEV1:
            return True
        if self.severity == Severity.SEV2:
            return self.customers_affected > 500 and self.duration_hours > 4
        return False

@dataclass
class PostMortem:
    ticket: IncidentTicket
    what_happened: str
    why_it_happened: str
    what_we_did: str
    what_changes: list

    def render(self) -> str:
        s = [f"POST-MORTEM {self.ticket.incident_id} — {self.ticket.system} "
             f"({self.ticket.severity.value}, blameless)",
             "-" * 68,
             "1. WHAT HAPPENED", f"   {self.what_happened}",
             "2. WHY IT HAPPENED", f"   {self.why_it_happened}",
             "3. WHAT WE DID", f"   {self.what_we_did}",
             "4. WHAT CHANGES"]
        s += [f"   - [{a.owner}] {a.description} (due {a.due})" for a in self.what_changes]
        s += ["", "TIMELINE"]
        s += [f"   {ts}  {ev}" for ts, ev in self.ticket.timeline]
        return "\n".join(s)

def main() -> None:
    print("=" * 72)
    print("17_incident_response — IR-2026-0042, end to end")
    print("=" * 72)

    t = IncidentTicket("IR-2026-0042", "customer-correspondence assistant")
    t.log("2026-06-03 09:12", "monitoring alert: schema-valid rate 94.1% vs 99.9% floor (control chart breach)")
    t.log("2026-06-03 09:26", "on-call confirms malformed outputs reaching the send queue; kill switch engaged")
    t.log("2026-06-03 09:31", "fallback to human-drafted correspondence; customer impact assessment started")
    t.log("2026-06-03 11:05", "root cause isolated: vendor foundation-model update changed JSON quoting behaviour")
    t.log("2026-06-03 13:40", "impact confirmed: 612 customers received malformed correspondence over 4.7 hours")
    t.log("2026-06-04 10:00", "post-mortem held (blameless); actions assigned")

    t.customers_affected, t.duration_hours = 612, 4.7
    t.severity = classify_severity(612, "critical", 4.7)
    print(f"\n[1] classification: {t.severity.value} "
          f"({t.customers_affected} customers, {t.duration_hours}h, critical operational severity)")
    assert t.severity == Severity.SEV1

    notify = t.requires_supervisory_notification()
    print(f"[2] notification rule (mechanical default): notify = {notify}")
    print("    -> SEV-1 presumed notifiable under SUP 15.3; the legal judgement remains with compliance.")
    assert notify

    t.actions = [
        Action("Platform", "pin foundation-model version; deployment refuses unpinned configs", "2026-06-10"),
        Action("Vendor mgmt", "invoke change-notice clause; obtain vendor changelog feed", "2026-06-17"),
        Action("2LoD", "add JSON-quoting regression case to the Ch 11 frozen baseline", "2026-06-12"),
        Action("Ops", "schema-validator hard-fail before send queue, not after", "2026-06-14"),
    ]
    pm = PostMortem(
        t,
        "The assistant emitted malformed correspondence for 4.7 hours after a silent vendor model update.",
        "The foundation-model version was not pinned; the output validator logged failures but did not block the send queue.",
        "Kill switch at T+14 min; fallback to human drafting; customer remediation letters issued same day.",
        t.actions)

    print("\n[3] rendered post-mortem\n")
    print(pm.render())

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""04_application_composition.py — Chapter 4 companion.

Artefact dataclass (version, vendor, pinned, config); LLMApplication with
by-class/vendor/firm accessors; trace_request producing the structured
nine-event trace for the credit-memo summariser worked example.
Standard library only.
"""
from dataclasses import dataclass, field

@dataclass
class Artefact:
    name: str
    cls: str
    version: str
    vendor: str = "firm"
    pinned: bool = True
    config: dict = field(default_factory=dict)

@dataclass
class LLMApplication:
    name: str
    artefacts: list

    def by_class(self, cls):
        return [a for a in self.artefacts if a.cls == cls]

    def by_vendor(self, vendor):
        return [a for a in self.artefacts if a.vendor == vendor]

    def firm_owned(self):
        return self.by_vendor("firm")

def trace_request(app: LLMApplication, request: str):
    fm = app.by_class("foundation_model")[0]
    em = app.by_class("embedding_model")[0]
    ri = app.by_class("retrieval_index")[0]
    pt = app.by_class("prompt_template")[0]
    ov = app.by_class("output_validator")[0]
    ap = app.by_class("application")[0]
    ev = []
    e = lambda stage, artefact, detail: ev.append(
        {"event": len(ev) + 1, "stage": stage, "artefact": f"{artefact.name}@{artefact.version}", "detail": detail})
    e("ingress", ap, f"request received ({len(request)} chars); schema check passed")
    e("pre-process", ap, "PII scan and injection-pattern guard passed")
    e("embed", em, "request embedded to 1,536-dim vector")
    e("retrieve", ri, f"top-5 chunks retrieved from snapshot {ri.config['snapshot']}")
    e("assemble", pt, f"prompt rendered; fingerprint {pt.config['fingerprint']}")
    e("generate", fm, f"completion at T={fm.config['temperature']}, seed pinned={fm.pinned}")
    e("validate", ov, "output schema valid; no fabricated-citation pattern")
    e("post-process", ap, "audit fields attached; telemetry emitted")
    e("egress", ap, "response returned to caller")
    return ev

def build_summariser() -> LLMApplication:
    return LLMApplication("credit-memo summariser", [
        Artefact("gpt-x-enterprise", "foundation_model", "2026-05-01", "VendorA", True,
                 {"temperature": 0.2, "max_tokens": 900}),
        Artefact("embed-large", "embedding_model", "3.1", "VendorA", True, {}),
        Artefact("policy-corpus", "retrieval_index", "2026-06-30", "firm", True,
                 {"snapshot": "2026-06-30T00:00Z", "chunks": 41_212}),
        Artefact("memo-template", "prompt_template", "2.3", "firm", True,
                 {"fingerprint": "a41c…9f2e"}),
        Artefact("memo-schema-validator", "output_validator", "1.4", "firm", True, {}),
        Artefact("summariser-service", "application", "0.9.12", "firm", True, {}),
    ])

def main() -> None:
    print("=" * 72)
    print("04_application_composition — what 'the application' actually means")
    print("=" * 72)
    app = build_summariser()
    print(f"\n[1] {app.name}: {len(app.artefacts)} artefacts")
    for a in app.artefacts:
        print(f"    {a.cls:>17}  {a.name}@{a.version}  vendor={a.vendor}  pinned={a.pinned}")
    print(f"\n[2] Accessors: vendor-supplied = {[a.name for a in app.by_vendor('VendorA')]}")
    print(f"               firm-owned      = {[a.name for a in app.firm_owned()]}")
    print("\n[3] trace_request: the nine-event structured trace")
    trace = trace_request(app, "Summarise the credit memo for Andy Bakery LIMITED, £88k / 36 months.")
    assert len(trace) == 9
    for t in trace:
        print(f"    {t['event']}. [{t['stage']:>12}] {t['artefact']:<28} {t['detail']}")
    print("\nEvery event above is a telemetry obligation; Chapter 5 develops the extraction machinery.")

if __name__ == "__main__":
    main()

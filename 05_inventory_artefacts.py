#!/usr/bin/env python3
"""05_inventory_artefacts.py — Chapter 5 companion.

inventory_artefacts(SystemDescription) -> [Artefact] with class, rationale,
priority. The three Section 5.7 case studies produce the seven-, four-, and
thirteen-artefact outputs discussed in the text. Standard library only.
"""
from dataclasses import dataclass, field

@dataclass
class SystemDescription:
    name: str
    has_rag: bool = False
    prompt_templates: int = 1
    output_validators: int = 1
    agent_tools: int = 0
    agent_memory: bool = False
    foundation_models: int = 1

@dataclass
class Artefact:
    name: str
    cls: str
    rationale: str
    priority: str  # HIGH / MEDIUM / LOW

def inventory_artefacts(s: SystemDescription):
    out = []
    for i in range(s.foundation_models):
        out.append(Artefact(f"{s.name}:fm{i+1}", "foundation_model",
                            "vendor-supplied generator; version and sampling config are risk-bearing", "HIGH"))
    out.append(Artefact(f"{s.name}:app", "application",
                        "firm wrapper code; hosts most preventive controls", "HIGH"))
    for i in range(s.prompt_templates):
        out.append(Artefact(f"{s.name}:prompt{i+1}", "prompt_template",
                            "behaviour-determining text; fingerprinted and versioned", "HIGH"))
    if s.has_rag:
        out.append(Artefact(f"{s.name}:embedder", "embedding_model",
                            "determines retrieval geometry; version changes move the corpus", "MEDIUM"))
        out.append(Artefact(f"{s.name}:index", "retrieval_index",
                            "snapshot is part of the effective input distribution", "MEDIUM"))
    for i in range(s.output_validators):
        out.append(Artefact(f"{s.name}:validator{i+1}", "output_validator",
                            "last preventive control before egress (schema/judge/HITL)", "HIGH"))
    for i in range(s.agent_tools):
        out.append(Artefact(f"{s.name}:tool{i+1}", "agent_tool",
                            "action surface; approval mode set by capability x reversibility", "HIGH"))
    if s.agent_memory:
        out.append(Artefact(f"{s.name}:memory", "agent_memory",
                            "persistent state; retention and content governed as first-class artefact", "MEDIUM"))
    return out

CASES = [
    SystemDescription("chatbot", has_rag=True, prompt_templates=2, output_validators=1),          # 7
    SystemDescription("summariser", has_rag=False, prompt_templates=1, output_validators=1),      # 4
    SystemDescription("kyc-agent", has_rag=False, prompt_templates=1, output_validators=1,
                      agent_tools=8, agent_memory=True),                                          # 13
]

def main() -> None:
    print("=" * 72)
    print("05_inventory_artefacts — from system description to inventory rows")
    print("=" * 72)
    expected = {"chatbot": 7, "summariser": 4, "kyc-agent": 13}
    for s in CASES:
        arts = inventory_artefacts(s)
        print(f"\n{s.name}: {len(arts)} artefacts (expected {expected[s.name]})")
        assert len(arts) == expected[s.name], (s.name, len(arts))
        for a in arts:
            print(f"    [{a.priority:<6}] {a.cls:>17}  {a.name:<22} {a.rationale}")
    print("\nOutputs load directly into the Chapter 6 inventory schema.")

if __name__ == "__main__":
    main()

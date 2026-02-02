# Agentic AI Workflow (CAM + Architecture Deltas)

This project's "agentic" behavior is a **deterministic orchestrator**: the **Canonical Architecture Model (CAM)** is the only architectural source of truth, and every proposed architecture change is an explicit **Architecture Delta (AD)** that must be **validated** and (typically) **approved** before it can be applied.

## Workflow diagram

```mermaid
graph TD
  Start["Start / resume run\nload CAM + rules + policy + overrides + state"]

  subgraph Origins[Delta origins - proposals only]
    Chat["User chat prompt"] --> CandAD
    Edit["Diagram edits (typed events)"] --> CandAD
    Analysis["Automated analysis\n(docs ingest + code grounding)"] --> CandAD
    Bootstrap["Bootstrap agent\n(nodes-only proposal)"] --> CandAD
    TreeSitter["Tree-sitter analysis\n(edges-only proposal)"] --> CandAD
  end

  Start --> CandAD["Candidate Architecture Delta - AD"]

  CandAD --> Validate["Validate AD\nstructure + archetype rules + CAM invariants + rule DSL + policy + overrides"]

  Validate -->|needs_clarification| Clarify["Ask blocking questions\nand revise AD"] --> CandAD
  Validate -->|invalid| Repair["Revise AD\nand re-validate"] --> CandAD

  Validate -->|valid| Approval["Approval gate\nApply delta"]
  Approval -->|approved| Apply["Apply AD to CAM\nappend cam/deltas/*; update cam/cam.json"]
  Approval -->|rejected| Rejected["Record rejection\nno CAM change"]

  Apply --> Views["Compile views from CAM only\nMermaid + DOT; non-authoritative"]

  Apply --> ExecPlan["Derive execution plan\nschema-validated; CAM mutation forbidden"]
  ExecPlan -->|user approves execution| Execute["Execution agents modify code only"]
  Execute --> Evidence["Post-exec grounding\n+ evidence capture"]
  Evidence --> StatusAD["Follow-up AD\nstatus and lifecycle transitions"] --> Validate

  Apply --> Workflow["Validate workflow slice\nrecord validated workflows"]
  Workflow --> WCount{Workflows at least 10}
  WCount -->|no| Loop["Continue - more proposals"] --> CandAD
  WCount -->|yes| Stop["Stop exploration\npolicy-enforced termination"]
```

## Notes (invariants reflected above)

- **CAM is authoritative**; diagrams are **views compiled from CAM only**. Editing a view can only yield a *candidate AD* (never a silent CAM change).
- **Diagram edit modes**: **design** edits produce typed events compiled into candidate AD ops; **correction** edits are view-only (layout/labeling) and cannot change CAM structure.
- **LLMs are stateless workers**: they may propose candidate deltas or execution steps, but they do not control approval gates, state transitions, or stop conditions.
- **AD validation outcomes** are `valid | invalid | needs_clarification`; applying is blocked unless the AD is `valid` and passes the approval gate (with known-debt overrides only downgrading violations when allowed by governance).
- **Execution is gated**: execution plans are schema-validated; execution agents change code only; CAM updates happen only via a follow-up AD with validation + approval.
- **Termination** is policy-enforced when validated workflows reach the target (default `10`).

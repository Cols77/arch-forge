# Agentic Architecture System — Implementation Plan (Webapp Archetype)

> **Status:** Active plan.
> **Archetype:** `webapp` (embedded driver archetype deferred).
> **Authority model:** **CAM is the only architectural truth**; diagrams are views; deltas are proposals; execution is gated.

---

## 0) Authoritative baselines (do not change)

### 0.1 Accepted design baseline

* **Diagram Editor Event Model (webapp archetype)** is **validated and approved** and must be treated as the baseline for future plan updates.

### 0.2 Canonical files (must exist in repo)

These are the authoritative policy/rules/schemas that the implementation must load and enforce:

* `rules/webapp.policy.json`
* `rules/webapp.rules.json`
* `schemas/execution_plan.schema.json`
* `docs/workflows.schema.json`

### 0.3 “Plan update” prompt to reuse

When updating this plan in the future, use the **existing plan update prompt** (the one that states the authoritative inputs and requires updating sections A–H). Keep it as the standard mechanism to regenerate/extend this document without rewriting from scratch.

---

## 1) System goals

Build an agentic system that:

* Maintains an **auditable Canonical Architecture Model (CAM)** for a web application.
* **Bootstraps the initial CAM from an existing codebase** using a constrained bootstrap agent (structure-only, review required).
* **Augments and reconciles CAM using Tree-sitter–derived edge candidates** (grounded, validated, optionally auto-applied per policy).
* Renders **diagrams as views** generated from CAM.
* Accepts **diagram edits** and **chat prompts** as *intent*, compiled into **Architecture Deltas (AD)**.
* Validates deltas against **rule DSL** + **policy layer**.
* Applies only explicitly approved deltas to CAM.
* After approved CAM changes, generates **Execution Plans** and allows **Codex/Claude-code-class models** to autonomously implement code changes **within strict boundaries**.

Non-goals (MVP):

* Multi-user permissions
* CI/CD integration
* Cross-archetype support (embedded driver archetype later)

---

## 2) Core concepts and authority boundaries

### 2.1 Canonical Architecture Model (CAM)

* **Single source of architectural truth**.
* Describes **structure + constraints**, not internal logic.
* Each node must include **logic references** (pointers to where internal behavior is defined):

  * code paths (folders/files), Markdown specs/ADRs sections.

CAM must support element lifecycle:

* `spec_only` → `implemented` → `deprecated`

### 2.2 Diagrams are views

* Diagrams are rendered **from CAM**.
* Diagram edits **do not mutate CAM directly**.
* Diagram edits emit **typed UI events** (baseline event model), compiled into candidate **Architecture Deltas**.

### 2.3 Architecture Delta (AD)

* An AD is a **proposal artifact** consisting of explicit operations (add node/edge, rename, change layer, remove edge, etc.).
* ADs can originate from:

  * UI diagram edits
  * user chat prompts
  * automation (bootstrap, tree-sitter)
* ADs must be **validated** before application.
* LLMs may **propose** ADs; they may **not apply** them.

### 2.4 Validation & governance

* Validation runs on:

  * webapp archetype constraints (types/layers)
  * rule DSL (`rules/webapp.rules.json`)
  * policy layer (`rules/webapp.policy.json`)

Governance constraints (hard):

* **Approval model:** single user, **explicit Apply button** required to apply delta to CAM and to start execution.
* **Overrides:** allowed only as **known debt**:

  * justification required
  * scoped (node/edge/rule/subgraph)
  * not permanent (expires/conditions)
  * triggers warnings in future runs until resolved
* **Auto-accept:**

  * bootstrap deltas: **require review**
  * tree-sitter deltas: **may auto-apply after validation**
* **Termination:** stop exploration when **validated workflows ≥ 10**.

---

## 3) Webapp archetype definition (current target)

### 3.1 Node types

* `component`, `service`, `interface`, `datastore`, `actor`

### 3.2 Edge types

* `depends_on`, `calls`, `reads`, `writes`, `publishes`, `subscribes`, `implements`

### 3.3 Layers

* `ui`, `app`, `domain`, `infra`

### 3.4 Minimum constraints (enforced)

* Allowed dependency directions:

  * `ui → app`
  * `app → domain`
  * `app → infra`
  * `domain → domain`
* Forbidden patterns:

  * `ui` must not `reads/writes` to `datastore` directly
  * `domain` must not depend on `infra`

---

## 4) Diagram editor workflow (baseline)

### 4.1 Event model (accepted)

The UI emits a closed set of typed events (baseline). Minimal MVP event set:

* Node events: `AddNode`, `RenameNode`, `ChangeLayer`
* Edge events: `AddEdge`, `RemoveEdge`

### 4.2 Modes

* **Design mode:** generates `spec_only` deltas (intent to evolve system).
* **Correction mode:** treats edits as model corrections; may require grounding runs.

### 4.3 Compilation

* UI events → candidate Architecture Delta ops (no direct CAM mutation).

### 4.4 Clarification loop

* If validation returns `needs_clarification`, the delta enters a clarification state.
* The system requests targeted user input.
* Clarifications update the delta and re-trigger validation before approval.

---

## 5) Validation system

### 5.1 Rule DSL

* Compact JSON rule format with:

  * `id`, `scope` (`node|edge|graph|policy|workflow`), `match`, `assert`, `severity`, `message`
* Rule evaluation is **deterministic** (stable ordering by `scope` then `id`).
* Graph-scope rules may bind across multiple nodes/edges (e.g., `same_nodes=true`).
* Example bug-catching rules are stored in `rules/webapp.rules.json`.

### 5.2 Policy layer

Enforced from `rules/webapp.policy.json`:

* Explicit approval gating
* Known-debt overrides (scoped, expiring, warning persistence)
* Auto-accept controls (treesitter ok; bootstrap requires review)
* Termination criterion: validated workflows ≥ 10

### 5.3 Known-debt override mechanics

* Overrides are stored as first-class artifacts (e.g., `cam/overrides/*.json`).
* Each override must specify:

  * `rule_id` or affected `node_ids`/`edge_ids`
  * justification (human-readable)
  * explicit scope (node | edge | rule | subgraph)
  * expiry condition (date or resolution condition)
* When an override matches a violation:

  * severity is downgraded from `error` → `warning`
  * the violation is tagged as **known debt**
* Known debt violations continue to emit warnings until the override expires or is resolved.

### 5.4 Actionable UI feedback contract

Validation must return:

* status: `valid | invalid | needs_clarification`
* violations with:

  * `rule_id`, severity, message
  * related node/edge IDs
  * suggested fixes

UI behavior:

* highlight offending elements
* block Apply when any `error` exists (unless overridden as known debt)
* show persistent warnings for known debt

---

## 6) Bootstrapping CAM from an existing codebase

### 6.1 Bootstrap agent role

* Populates CAM with **grounded structural facts** only.
* Outputs a **Bootstrap Delta** (proposal), never writes CAM directly.

### 6.2 Bootstrap contract (hard limits)

Allowed:

* `add_node` only (status `implemented`)
* attach `logic_refs` and code evidence (path + line range)
* tentative layer assignment (best-effort) with low confidence

Forbidden:

* invent responsibilities
* add edges broadly
* infer architecture boundaries

### 6.3 Allowed heuristics (whitelist)

* folder/package boundaries → candidate components
* framework detection → suggest node type / tentative layer
* datastore detection (ORM configs, client imports) → datastore nodes
* entrypoint detection → primary component candidates

### 6.4 Review requirement

* Bootstrap deltas **must be reviewed** and approved explicitly (policy).

---

## 7) Tree-sitter integration (grounding engine)

Role:

* Extract **evidence-backed candidate edges** from code syntax.

Constraints:

* Tree-sitter proposes only these edge types: `depends_on`, `calls`, `implements`, `reads`, `writes`, `publishes`, `subscribes`.
* Tree-sitter does not create nodes or assign layers.
* All results go through validation.

### 7.1 Symbol-to-CAM mapping

* Raw symbols/files are mapped to CAM nodes via ownership rules:

  * folder/package containment
  * explicit ownership configuration (overridable by user)
* Mapping is explicit and auditable; incorrect mappings are corrected via **Correction mode** deltas.

### 7.2 Edge candidate filtering

* Ignore intra-file and intra-component calls by default.
* Propose only **cross-component** edges.
* Apply thresholds (e.g., top-K edges per component) to prevent edge explosion.

Policy:

* Tree-sitter deltas **may auto-apply** if validation passes (configurable), but large diffs should be reviewable.

---

## 8) Execution phase (autonomous code modification)

### 8.1 Preconditions

Execution is allowed only if:

* the relevant Architecture Delta has been **validated** and **applied to CAM**
* the user has explicitly approved starting execution (button)

### 8.2 Execution plan

* Execution must be driven by a machine-readable plan validated against `schemas/execution_plan.schema.json`.
* The execution plan references:

  * `cam_version`
  * `applied_delta_ids`
  * the scope (CAM nodes/edges)

### 8.3 Executor constraints

Executors (Codex/Claude-code-class) are **implementers only**:

* Must not introduce new CAM nodes/edges without a new delta
* Must not modify unrelated modules outside the declared scope
* Must produce evidence for each implemented item (file path + line ranges + symbol/callsite)

### 8.4 Execution report & reconciliation

* Executors must emit a structured **Execution Report**:

  * files changed
  * tests run and results
  * evidence produced per CAM node/edge
  * scope violations (if any)
* The orchestrator validates the report and produces a **follow-up CAM delta** proposing:

  * status transitions (`spec_only → implemented`)
  * evidence attachment
* Applying this CAM update delta requires explicit approval.

### 8.5 Rollback

* Rollback strategy is `git reset/revert`.
* Trigger rollback if:

  * tests fail
  * validation regresses
  * execution violates declared scope

---

## 9) Workflows and termination

### 9.1 Workflow definition

A workflow is a named slice stored in CAM, following `docs/workflows.schema.json`.

### 9.2 Workflow validation contract

A workflow is **validated** only if:

* all nodes and edges in the slice are `implemented`
* no validation `error` applies within the slice
* required evidence exists for all elements
* associated tests (if defined) pass

Validation is an explicit user action ("Validate workflow").

### 9.3 Termination criterion

* Architecture exploration/bootstrapping loops stop when **validated workflows ≥ 10**.

---

## 10) Repository deliverables (MVP)

Additional required artifacts:

* Known-debt overrides (e.g., `cam/overrides/*.json`)
* Execution reports (e.g., `execution/reports/*.json`)

Must-have artifacts:

Must-have artifacts:

* CAM file (e.g., `cam/cam.json`)
* Delta history (e.g., `cam/deltas/*.json`)
* Rules + policy (already specified)
* Diagram outputs (e.g., `diagrams/*.mmd`, `diagrams/*.dot`)
* Execution plans + reports (e.g., `execution/plans/*.json`, `execution/reports/*.json`)

---

## 11) Next implementation milestones

### MVP1 — CAM + diagrams + deltas

* CAM schema + storage
* diagrams rendered from CAM
* diagram editor emits baseline events and compiles to delta
* validation engine + UI feedback

### MVP2 — bootstrap + tree-sitter grounding

* bootstrap agent outputs bootstrap delta (review required)
* tree-sitter edge candidates + optional auto-apply after validation

### MVP3 — execution

* execution plan generator + schema validation
* executor integration (Codex/Claude-code-class)
* evidence capture + CAM status update proposal

---

# Implementation Plan: Auditable System-Understanding Diagrams

## Scope (current)
- **[ADDED]** Focus archetype: **web application** only.
- **[ADDED]** Layers (web app): `ui`, `app`, `domain`, `infra`.
- **[ADDED]** Non-goal (for now): define other archetypes; only add extension seams so new archetypes can be added later without rewriting the workflow.

## Authoritative baselines (do not change)
- **[ADDED]** Canonical policy/rules/schemas that must exist and be enforced:
  - `rules/webapp.policy.json`
  - `rules/webapp.rules.json`
  - `schemas/execution_plan.schema.json`
  - `docs/workflows.schema.json`
- **[ADDED]** Diagram editor event model (webapp archetype) is an accepted baseline and must remain a closed set:
  - Node events: `AddNode`, `RenameNode`, `ChangeLayer`
  - Edge events: `AddEdge`, `RemoveEdge`
- **[ADDED]** Termination target for architecture exploration is `target_validated_workflows = 10` (set/enforced via policy; not by agents/prompts).

## Phase 0 - Existing Codebase Assessment

### Summary of what already exists
- Languages/frameworks: Python + FastAPI service, SQLite persistence, HTML/CSS/JS UI, JSON eval cases.
- RAG stack: Qdrant vector store client, ingestion pipeline, embeddings adapter with deterministic fallback, retrieval helper.
- LLM access: HTTP client for chat completions; config for OpenAI-compatible endpoints.
- Evaluation CLI: `scripts/run_eval.py` and `app/eval/runner.py`.

### What can be reused as-is
- Qdrant client wrapper and collection management (`app/rag/vector_store.py`).
- Embeddings adapter and cache (`app/rag/embeddings.py`).
- Logging/metrics scaffolding (`app/observability/*`) and config loader (`app/config.py`).

### What exists but needs extension or refactoring
- Ingestion is paragraph-based and does not record Markdown headings or line ranges; must add provenance capture for specs/tickets/notes.
- Retrieval returns only text and scores; must return structured provenance and doc metadata.
- Qdrant usage is tuned to a chat assistant; needs a separate docs collection or tenant for diagram inputs.
- README references `make` but no Makefile exists; CLI entrypoint for diagram pipeline is missing.

### Gaps, overlaps, and partially implemented features
- **[MODIFIED]** Overlap: current RAG pipeline can store Markdown, but it is not tied to a CAM/IR bundle or diagram compiler.
- **[MODIFIED]** Gap: no deterministic orchestrator/state machine, no CAM + delta workflow, no diagram generation-from-CAM.
- Partial: agent logic exists for chat but is not a workflow controller and is not deterministic.
- Gap: adjacent legacy project at `../visitor-assistant` is not assessed; needs cleanup planning to avoid cross-project confusion.

### What is genuinely missing
- **[MODIFIED]** Canonical Architecture Model (CAM) as the only architectural source of truth, with evidence and lifecycle state.
- Deterministic orchestrator with typed step outputs, validators, repair loops, and persistent state.
- Code-grounding pipeline (rg + tree-sitter, with optional LSP later) and symbol extraction.
- Diagram compilation (views) to Mermaid and Graphviz DOT (rendered from CAM only).
- Docker Compose for Qdrant container and diagram pipeline CLI.
- Cleanup plan for legacy project artifacts in `../visitor-assistant` (removal).

## A) Repository structure (target state)

**Reuse**
- `app/rag/*` for embeddings and Qdrant access.
- `app/observability/*` for structured logging.

**Extend**
- `app/config.py` to add diagram-system settings (CAM/IR paths, docs collection, index paths).
- **[MODIFIED]** `app/diagram_ir/` to evolve from a generic "diagram IR" into the **CAM + Architecture Delta** model layer (schema, validators, load/save, delta apply, audit log), while remaining deterministic.

**New**
- **[ADDED]** `app/archetypes/web_app/` (web-app-specific node/edge/layer rules, layering validators, forbidden dependency pattern validators).
- `app/orchestrator/` (deterministic state machine, step outputs, repair logic).
- `app/docs_ingest/` (Markdown/ticket/note parsing, provenance extraction, Qdrant ingestion).
- `app/grounding/` (rg-based code search, optional symbol index adapters).
- **[MODIFIED]** `app/diagram_compile/` (CAM -> Mermaid/DOT "views"; diagram-edit parsing/diff to produce candidate Architecture Deltas; view-only layout hints live outside CAM).
- **[ADDED]** `app/execution/` (execution-plan schema + guardrails for "execution agents"; explicitly forbids CAM mutation).
- `scripts/diagram_build.py` (CLI entrypoint).
- `docker/docker-compose.yml` (Qdrant container).
- **[ADDED]** `cam/` (authoritative CAM snapshot + governance artifacts):
  - `cam/cam.json` (current CAM snapshot; diagram compilers read this only)
  - `cam/deltas/*.json` (append-only Architecture Delta history)
  - `cam/overrides/*.json` (known-debt overrides)
- **[ADDED]** `rules/` (authoritative rule DSL + policy):
  - `rules/webapp.rules.json`
  - `rules/webapp.policy.json`
- **[ADDED]** `schemas/` (machine-readable contracts):
  - `schemas/execution_plan.schema.json`
  - (Optional) `schemas/architecture_delta.schema.json`, `schemas/known_debt_override.schema.json` (repo-internal validation only)
- **[ADDED]** `docs/workflows.schema.json` (workflow slice schema; loaded by validators/UI)
- **[ADDED]** `diagrams/` (rendered views only; always derived from CAM)
- **[ADDED]** `execution/` (executor artifacts; never authoritative):
  - `execution/plans/*.json`
  - `execution/reports/*.json`
- **[ADDED]** `out/` (cache/state for deterministic runs; safe to delete):
  - `out/state.json`
  - `out/views/*.mmd|*.dot` (optional build artifacts; non-authoritative)

## B) Docker & runtime architecture

**Reuse**
- Existing Qdrant URL configuration in `app/config.py` (`QDRANT_URL`).

**Extend**
- Add `DOCS_QDRANT_COLLECTION` (must be separate from chat RAG collection).

**New**
- `docker-compose.yml` to run Qdrant separately.
- Example commands:
  ```bash
  docker-compose -f docker/docker-compose.yml up -d qdrant
  python scripts/diagram_build.py --repo . --docs ./docs --tickets ./tickets --notes ./notes --ir ./cam/cam.json
  ```

## C) Canonical Architecture Model (CAM) (authoritative) + IR bundle (storage)

**Reuse**
- None.

**Extend**
- **[MODIFIED]** Use existing logging and config for CAM/IR versioning and output location.

**New**

### Canonical Architecture Model (CAM)
- **[ADDED]** CAM is the **ONLY source of architectural truth**.
  - Diagrams are rendered *from* CAM ("views"), never treated as authority.
  - Diagram edits never mutate CAM; they emit **candidate Architecture Deltas (ADs)** only.
  - CAM models **structure + allowed relationships + rules/invariants**, not internal business logic.
- **[ADDED]** Append-only update semantics:
  - CAM is updated only by applying validated Architecture Deltas (no direct edits).
  - Every applied delta is persisted immutably under `cam/deltas/` and referenced from `cam/cam.json`.
  - The current `cam/cam.json` snapshot is reproducible from (initial snapshot + ordered delta log).
- **[ADDED]** CAM must not embed business logic:
  - Allowed: high-level responsibility statements, ownership, contracts, and pointers.
  - Forbidden: algorithm steps, detailed control flow, data transformations, or "how it works" descriptions (those must live in the referenced specs/code).
- **[ADDED]** CAM elements (web app archetype):
  - Node types: `component`, `service`, `interface`, `datastore`, `actor`
  - Edge types: `depends_on`, `calls`, `reads`, `writes`, `publishes`, `subscribes`, `implements`
  - Layers: `ui`, `app`, `domain`, `infra`
- **[ADDED]** CAM rules/invariants (minimum non-negotiable set for `web_app`):
  - Allowed layer dependencies:
    - `ui -> app`
    - `app -> domain`
    - `app -> infra`
    - `domain -> domain`
  - Forbidden dependency patterns:
    - `ui` must **NOT** `reads`/`writes` any `datastore` directly
    - `domain` must **NOT** depend on `infra` (for any edge type that expresses dependency)
  - **[CLARIFIED]** Any additional allowed transitions/patterns must be introduced by **versioned archetype rules** (not ad hoc, and never via diagram edits).
- **[ADDED]** Logic reference strategy (link, don't model):
  - CAM nodes/edges MUST include `logic_refs` pointing to where internal logic/spec decisions live:
    - code paths (file + line range + symbol/callsite where possible)
    - Markdown specs (file + heading + line range)
    - ADRs (Markdown decision records)
  - These references are required even when the element is `spec_only` (spec references are acceptable before code exists).

### Lifecycle (architectural intent) vs evidence `status` (grounding confidence)
- **[ADDED]** Lifecycle (CAM intent): `spec_only -> implemented -> deprecated`
  - `spec_only`: intended/approved architecture that is not yet implemented
  - `implemented`: architecture is present in code (backed by code-grounding evidence)
  - `deprecated`: still present but planned for removal/replacement (must link to ADR/spec explaining why)
- **[CLARIFIED]** Evidence `status` remains the diagram compiler driver (for styling/omission) and remains constrained to:
  - `implemented | spec_only | inferred | unknown`
- **[ADDED]** Invariants:
  - Lifecycle transitions are only performed by applying validated deltas (including "mark implemented" deltas after execution + grounding evidence).
  - `logic_refs` are mandatory for nodes/edges; missing refs are a validation error.
  - Diagrams must compile from CAM only; views are never authoritative.

### Example CAM/IR bundle fragment (web app archetype)
```json
{
  "version": "2.0",
  "archetype": "web_app",
  "generated_at": "2026-01-31T20:30:00Z",
  "nodes": [
    {
      "id": "svc.ingest",
      "label": "Ingestion API",
      "type": "service",
      "layer": "app",
      "lifecycle": "implemented",
      "status": "implemented",
      "logic_refs": [
        {
          "kind": "code",
          "file": "app/api/ingest.py",
          "lines": [1, 120],
          "symbol": "ingest_endpoint"
        },
        {
          "kind": "adr",
          "file": "specs/adr/0002-ingestion-api.md"
        }
      ],
      "provenance": {
        "kind": "code",
        "file": "app/api/ingest.py",
        "lines": [1, 120],
        "symbol": "ingest_endpoint"
      }
    },
    {
      "id": "store.qdrant_docs",
      "label": "Qdrant Docs Index",
      "type": "datastore",
      "layer": "infra",
      "lifecycle": "implemented",
      "status": "implemented",
      "logic_refs": [
        {
          "kind": "code",
          "file": "app/rag/vector_store.py",
          "lines": [1, 240],
          "symbol": "QdrantVectorStore"
        }
      ],
      "provenance": {
        "kind": "code",
        "file": "app/rag/vector_store.py",
        "lines": [1, 240],
        "symbol": "QdrantVectorStore"
      }
    }
  ],
  "edges": [
    {
      "from": "svc.ingest",
      "to": "store.qdrant_docs",
      "type": "writes",
      "lifecycle": "implemented",
      "status": "implemented",
      "logic_refs": [
        {
          "kind": "markdown",
          "file": "specs/adr/0002-ingestion-api.md",
          "heading": "Persistence",
          "lines": [42, 88]
        }
      ],
      "provenance": {
        "kind": "markdown",
        "file": "specs/adr/0002-ingestion-api.md",
        "heading": "Persistence",
        "lines": [42, 88]
      }
    }
  ],
  "applied_deltas": [
    {
      "delta_id": "ad.0001"
    }
  ]
}
```

### Extensibility (archetypes)
- **[ADDED]** Archetype-specific logic lives under `app/archetypes/<archetype_name>/`.
- **[ADDED]** The AD lifecycle, approval gates, CAM storage, and execution boundaries are archetype-agnostic; only these components are archetype-specific:
  - node/edge/layer enums and required fields
  - structural constraints and forbidden dependency pattern validators
  - view rendering rules (e.g., styling conventions)
- **[ADDED]** Adding a future archetype is done by adding a new archetype package + validators and selecting it via `archetype`; the delta workflow and guardrails stay unchanged.

## D) Orchestrator workflow (state machine)

**Reuse**
- None (current agent flow is not deterministic).

**Extend**
- Use existing observability utilities for step-level tracing.

**New**
- Deterministic state machine with typed outputs and validators.
- Explicit state persistence (e.g., `out/state.json`) to support restartable runs.
- **[CLARIFIED]** LLMs are stateless workers: they may propose candidate deltas or execution steps, but never control workflow, approval, state transitions, or stop conditions.

### Architecture Delta (AD) lifecycle (proposal -> validate -> approve -> apply)
- **[ADDED]** Deltas are explicit proposal artifacts; origins:
  - user chat prompts
  - diagram edits
  - automated analysis (docs ingestion + code grounding)
- **[ADDED]** Deltas describe operations only (add/remove node/edge, set attribute, etc.).
- **[ADDED]** Validation outcomes (tri-state):
  - `valid`
  - `invalid` (with violations)
  - `needs_clarification` (blocking questions)
- **[ADDED]** Only validated + approved deltas may be applied to CAM.
- **[ADDED]** LLMs may propose deltas but may NOT apply them.

#### Example Architecture Delta artifact
```json
{
  "delta_id": "ad.0002",
  "archetype": "web_app",
  "origin": { "kind": "diagram_edit", "ref": "out/views/webapp-main.mmd" },
  "intent": "Add Payments service and datastore",
  "ops": [
    {
      "op": "add_node",
      "node": {
        "id": "svc.payments",
        "label": "Payments Service",
        "type": "service",
        "layer": "app",
        "lifecycle": "spec_only",
        "status": "spec_only",
        "logic_refs": [{ "kind": "adr", "file": "specs/adr/0004-payments.md" }]
      }
    },
    {
      "op": "add_node",
      "node": {
        "id": "db.payments",
        "label": "Payments DB",
        "type": "datastore",
        "layer": "infra",
        "lifecycle": "spec_only",
        "status": "spec_only",
        "logic_refs": [{ "kind": "adr", "file": "specs/adr/0004-payments.md" }]
      }
    },
    {
      "op": "add_edge",
      "edge": {
        "from": "svc.payments",
        "to": "db.payments",
        "type": "writes",
        "lifecycle": "spec_only",
        "status": "spec_only",
        "logic_refs": [{ "kind": "adr", "file": "specs/adr/0004-payments.md" }]
      }
    }
  ]
}
```

### Validation & authority rules (web app archetype)
- **[MODIFIED]** All deltas must be validated against:
  - CAM structural constraints (IDs, types, required fields, no dangling references)
  - web-app layering rules + forbidden dependency patterns
  - CAM invariants (including "no business logic in CAM" and "logic_refs required")
  - rule DSL (`rules/webapp.rules.json`) with deterministic evaluation
  - policy layer (`rules/webapp.policy.json`) enforcing approval gates, auto-accept controls, and termination targets
- **[ADDED]** Validation emits a machine-readable report with violation codes; apply is blocked if not `valid`.
- **[ADDED]** Only validated deltas may be considered for approval; only approved deltas may be applied.

### Rule DSL + policy layer (governance)
- **[ADDED]** Rule DSL is an authoritative, version-controlled artifact (`rules/webapp.rules.json`) with deterministic evaluation order (stable ordering by `scope` then `id`).
  - Rule shape: `id`, `scope` (`node|edge|graph|policy|workflow`), `match`, `assert`, `severity`, `message`
- **[ADDED]** Policy is an authoritative, version-controlled artifact (`rules/webapp.policy.json`) that enforces:
  - explicit approval gates (Apply delta, Start execution)
  - auto-accept controls by delta origin (`bootstrap` requires review; `tree_sitter` may auto-apply after validation)
  - known-debt override requirements (justification, scope, expiry, warning persistence)
  - termination criterion: validated workflows >= `target_validated_workflows` (default 10)
- **[ADDED]** Validation result contract (UI + CLI):
  - status: `valid | invalid | needs_clarification`
  - violations: `rule_id`, severity, message, related node/edge IDs, and suggested fixes
  - Apply is blocked when any `error` remains after known-debt override evaluation.

### Known-debt overrides (governance escape hatch)
- **[ADDED]** Overrides are stored as first-class artifacts under `cam/overrides/*.json`.
- **[ADDED]** Each override MUST specify: affected `rule_id` and/or `node_ids`/`edge_ids`, justification, explicit scope (node|edge|rule|subgraph), and an expiry condition (date or resolution condition).
- **[ADDED]** When an override matches a violation:
  - severity is downgraded from `error` -> `warning`
  - the violation is tagged as known debt and remains a persistent warning until expiry/resolution

### User chat integration (chat -> candidate deltas)
- **[ADDED]** Chat prompts become candidate deltas only (never direct CAM edits).
- **[ADDED]** Ambiguity handling:
  - If required details are missing (node `type`, `layer`, edge `type`, IDs, or unclear targets), return `needs_clarification` and ask concrete questions.
  - Clarification responses create a revised delta; re-validate from scratch.
- **[ADDED]** Approval flow:
  - The user approves the exact validated delta (by ID) before CAM is updated.
  - Approval is explicit and auditable (no "auto-apply" of LLM suggestions).

### Execution phase (code modification) and autonomy boundaries
- **[ADDED]** Code changes may be planned/executed only after a delta is applied to CAM.
- **[ADDED]** Codex / Claude Code-class models are used ONLY as execution agents:
  - MUST follow an explicit execution plan derived from (CAM + applied deltas).
  - Execution plans are machine-readable, schema-validated against `schemas/execution_plan.schema.json`, and stored under `execution/plans/`.
    - The execution plan MUST include: `cam_version`, `applied_delta_ids`, and `scope` (node/edge IDs).
  - MUST NOT invent architecture (no new nodes/edges/layers beyond applied deltas).
  - MUST NOT apply deltas or edit CAM directly.
- **[ADDED]** Execution must update:
  - implementation (code changes)
  - grounding evidence (code provenance updates for the affected nodes/edges)
  - logic_refs (point to the new/changed code/spec/ADR)
  - CAM lifecycle/status transitions via a follow-up delta (e.g., mark new elements `implemented` once evidence exists)
- **[ADDED]** Post-execution, the orchestrator:
  - re-runs grounding and validators
  - validates the executor's machine-readable Execution Report (stored under `execution/reports/`) including:
    - files changed
    - tests run and results
    - evidence produced per CAM node/edge (file + line range + symbol/callsite where possible)
    - scope violations (if any)
  - generates a "status transition delta" (spec_only -> implemented) backed by evidence
  - validates it and requires approval (or an explicitly configured, auditable auto-approval policy)

### Example state record (delta gates)
```json
{
  "run_id": "2026-01-31T20:30:00Z",
  "state": "validate_deltas",
  "inputs_hash": "...",
  "pending_deltas": ["ad.0002"],
  "validated_deltas": [],
  "applied_deltas": ["ad.0001"],
  "last_success": {
    "ingest_markdown": "2026-01-31T20:30:10Z",
    "index_code": "2026-01-31T20:30:20Z"
  }
}
```

## E) Retrieval strategy (Markdown-first)

**Reuse**
- Qdrant access and embeddings cache.

**Extend**
- Ingestion to include `doc_type`, `heading`, `line_start`, `line_end` in Qdrant payloads.

**New**
- Markdown/ticket/note collectors with explicit globs:
  - `docs/**/*.md`, `tickets/**/*.{md,txt}`, `notes/**/*.{md,txt}`
- Chunking by heading + paragraph to preserve provenance.
- **[ADDED]** Retrieved evidence may propose candidate deltas (e.g., "spec mentions a component not in CAM"), but may never update CAM without going through the AD lifecycle.
- Example rg command to seed candidates:
  ```bash
  rg -n "component|service|flow|API|diagram" docs tickets notes
  ```

## F) Grounding strategy (code truth)

**Reuse**
- None.

**Extend**
- **[MODIFIED]** Integrate rg search results into CAM evidence extraction and candidate delta generation (analysis-origin deltas).

**New**
- Default: `rg`-based code grounding plus a standalone tree-sitter CLI indexer for richer symbol metadata.
- Tree-sitter is the preferred symbol indexer; use it to capture definitions, references, and callsites via a separate CLI tool.
- Example commands:
  ```bash
  rg -n "class|def|fn|interface|struct" app src
  tree-sitter-index --repo . --out out/symbols.json
  ```
- Code retrieval is not Qdrant-backed unless explicitly enabled later.
- **[ADDED]** Automated code analysis may originate candidate deltas (e.g., detected forbidden dependency), but must never apply them directly; it must emit ADs + validation reports.
- **[ADDED]** Bootstrap agent (structure-only, nodes-only) emits a Bootstrap Delta (proposal), never writes CAM directly.
  - Allowed: `add_node` only (status `implemented`), attach `logic_refs` + code evidence, tentative layer assignment (best-effort, low confidence).
  - Forbidden: invent responsibilities, add edges broadly, infer architecture boundaries.
  - Governance: bootstrap deltas must be reviewed and explicitly approved (policy; no auto-apply).
- **[ADDED]** Tree-sitter deltas are edges-only and evidence-backed.
  - Constraints: Tree-sitter proposes only edge candidates; it MUST NOT create nodes or assign layers.
  - Filtering: ignore intra-file and intra-component calls by default; propose cross-component edges only; apply top-K thresholds per component to avoid edge explosion.
  - Governance: tree-sitter deltas may auto-apply after validation if enabled by policy; large diffs must remain reviewable.

## G) Diagram workflow (views) + compilation

**Reuse**
- None.

**Extend**
- None.

**New**
- **[MODIFIED]** Compile strictly from CAM; no elements outside CAM may appear.
- **[ADDED]** Diagrams are views, not authority:
  - Views are rendered from CAM.
  - Editing a view can never "silently" change CAM; it yields a candidate Architecture Delta that must be validated and approved.
  - View-only changes (layout hints) are stored separately from CAM and do not affect validation.
- **[ADDED]** Design mode vs correction mode:
  - **Design mode**: diagram edits intentionally propose structural changes -> emit candidate ADs.
  - **Correction mode**: diagram edits are limited to view-only metadata (layout/labeling); any structural edit is blocked and redirected to design mode (or requires explicit AD creation).
- **[ADDED]** Diagram editor event pipeline (events -> candidate delta):
  - Diagram edits emit typed events (baseline closed set) and are compiled deterministically into delta ops.
  - The event stream is append-only (persisted as an auditable artifact) and references the source diagram/view.
  - Delta review UX must provide: validation status, violation list, and a single explicit Apply button (blocked on non-overridden errors).
  - Delta preview is rendered as a temporary overlay (CAM + candidate delta) for review; only post-apply views are written under `diagrams/`.
- Line style mapping by evidence `status`:
  - implemented: solid
  - spec_only: dashed
  - inferred: dotted
  - unknown: not drawn
- Example Mermaid output:
  ```mermaid
  graph TD
    svc_ingest["Ingestion API"]
    store_docs["Qdrant Docs Index"]
    svc_ingest -->|writes| store_docs
    linkStyle 0 stroke-dasharray: 5 5;
  ```
- Example DOT output:
  ```dot
  digraph G {
    "svc.ingest" [label="Ingestion API"];
    "store.qdrant_docs" [label="Qdrant Docs Index"];
    "svc.ingest" -> "store.qdrant_docs" [style=dashed,label="writes"];
  }
  ```

## H) Incremental updates & termination

**Reuse**
- None.

**Extend**
- Use SQLite or JSON file for cache/state tracking.

**New**
- File hashing for docs and code; re-run only changed inputs.
- **[MODIFIED]** Deterministic run termination: CAM validates, all approved deltas are applied (or explicitly rejected), and no repair/clarification tasks are pending.
- **[ADDED]** Architecture exploration termination: stop proposing/auto-applying new deltas when validated workflows >= `target_validated_workflows` (default 10; enforced by policy).
- **[ADDED]** Repair/clarification loops apply to:
  - CAM validation failures (structural + archetype constraints)
  - delta validation failures (invalid or needs clarification)
  - missing `logic_refs` (structural element exists but has no pointers to logic/spec)
- **[ADDED]** Workflows (validated slices)
  - Workflows are named CAM slices following `docs/workflows.schema.json` (stored in CAM).
  - "Validate workflow" checks:
    - all nodes/edges in the slice are `implemented`
    - no validation `error` applies within the slice (after overrides)
    - required evidence exists for all elements
    - associated tests (if defined) pass
  - A workflow counts toward termination only when validation passes and is recorded persistently (e.g., in CAM metadata and/or state).

## I) MVP roadmap

**Reuse**
- Use existing Qdrant client, embeddings adapter, and logging as-is.

**Extend**
- Ingestion to emit provenance-rich chunks and to target a dedicated docs collection.
- Config updates to add docs collection name, CAM/IR path, and CLI defaults.

**New**
1) Cleanup planning for `../visitor-assistant`: inventory files, confirm removal scope, execute removal, update ignores/README to prevent reuse.
2) **[MODIFIED]** CAM schema (web app archetype) + validators + persistence (CAM is authoritative; diagrams are views; CAM is append-only via applied deltas).
3) **[ADDED]** Governance + deltas: Architecture Delta schema + validation + approval + apply pipeline (rule DSL + policy; known-debt overrides; bootstrap review vs tree-sitter auto-apply).
4) Markdown/ticket/note ingestion with heading-based chunking and provenance capture.
5) Code grounding via rg + tree-sitter symbol extraction.
6) **[MODIFIED]** Deterministic orchestrator with explicit design/correction modes, delta gates, and restartable state.
7) **[MODIFIED]** CAM-to-Mermaid and CAM-to-DOT compilers with status-aware styling (views only).
8) **[ADDED]** Chat -> candidate delta extraction + clarification workflow (`needs_clarification` outcome).
9) **[ADDED]** Execution-phase gate: derive execution plans from applied deltas; execution agents modify code only; post-exec grounding produces status-transition deltas.
10) CLI runner and docker-compose for Qdrant.
11) Minimal test suite: CAM validators, delta validators, diagram compiler output, provenance extraction.
12) **[ADDED]** Workflows: define workflow schema + storage in CAM, add "Validate workflow" action, enforce termination when validated workflows >= 10.

### Roadmap task specs (new/modified items)

**Task 2 - CAM schema + validators + persistence (append-only)**
- Inputs: existing `app/diagram_ir/*`, repo codebase, specs/ADRs referenced by `logic_refs`.
- Outputs: `cam/cam.json` (authoritative snapshot), CAM load/save/validate APIs, delta apply/replay support.
- Dependencies: `app/archetypes/web_app/` (node/edge/layer enums + validators).
- Acceptance criteria:
  - `cam/cam.json` round-trips (load->save->load) without data loss.
  - Missing required fields (e.g., `logic_refs`) fail validation deterministically with actionable errors.
  - Applying a fixed delta log reproduces the same `cam/cam.json` snapshot deterministically.
- Traceability: Canonical Architecture Model (CAM); enforces single source of truth, append-only updates via Architecture Deltas, nodes/edges link to internal logic via pointers only.

**Task 3 - Governance + deltas (rules/policy/overrides/approval/apply)**
- Inputs: candidate delta (from diagram events/chat/bootstrap/tree-sitter), `cam/cam.json`, `rules/webapp.rules.json`, `rules/webapp.policy.json`, `cam/overrides/*.json`.
- Outputs: validation report JSON, explicit approval record, applied delta stored under `cam/deltas/`, updated `cam/cam.json`.
- Dependencies: Task 2; deterministic rule evaluator; policy loader.
- Acceptance criteria:
  - Validation order and output are deterministic for the same inputs (stable ordering; stable violation codes).
  - Apply is blocked when any non-overridden `error` exists; known-debt overrides downgrade error->warning only when justified/scoped/not-expired.
  - Bootstrap deltas are review-required (no auto-apply); tree-sitter deltas may auto-apply only if enabled by policy and validation passes.
  - Diagram edits emit typed events and compile deterministically into delta ops; no direct CAM mutation from the UI.
- Traceability: Architecture Deltas + Diagrams + Validation & Governance; enforces typed-event->delta compilation, deterministic rule DSL evaluation, known-debt override scoping/expiry, explicit Apply gating, origin-specific auto-accept policy.

**Task 9 - Execution-phase gate (plans/reports/reconciliation)**
- Inputs: applied delta IDs, CAM version, explicit scope (node/edge IDs), executor model selection.
- Outputs: schema-validated execution plans under `execution/plans/`, schema-validated execution reports under `execution/reports/`, follow-up status-transition delta for CAM updates.
- Dependencies: Task 3 (approved/applied deltas + policy); grounding evidence pipeline for code provenance.
- Acceptance criteria:
  - Execution is blocked unless the relevant delta is applied and the user explicitly approves starting execution.
  - Execution plans validate against `schemas/execution_plan.schema.json` and constrain file/module scope.
  - Executor output includes evidence (file + line range + symbol/callsite when possible) and tests run; orchestrator validates the report.
  - CAM lifecycle/status transitions occur only via a follow-up delta that requires approval.
- Traceability: Execution Phase; enforces machine-readable plan, executor-only role, evidence+report requirement, status transitions via delta + approval.

**Task 12 - Workflows (validated slices) + termination**
- Inputs: workflow definitions (per `docs/workflows.schema.json`), CAM + evidence, test definitions (if any) referenced by workflows.
- Outputs: persisted validated workflow records + counts; policy-enforced stop condition when validated workflows >= 10.
- Dependencies: Task 2 (workflows stored in CAM); Task 3 (validation + overrides); test runner integration.
- Acceptance criteria:
  - "Validate workflow" enforces the workflow validation contract (implemented-only, no errors after overrides, evidence present, tests pass).
  - Validated workflows are recorded persistently and counted deterministically.
  - Automated exploration (bootstrap/tree-sitter/chat suggestions) is disabled when validated workflows >= `target_validated_workflows` (default 10), as enforced by policy.
- Traceability: Termination + Validation & Governance; enforces validated-workflows>=10 stop condition and persistent validation results.

## Risks and mitigations
- False positives from rg or doc parsing: require provenance and validator checks before acceptance.
- **[MODIFIED]** Diagram drift: only compile from CAM, and block any diagram output if CAM validation fails.
- **[ADDED]** Diagram edits causing silent architecture changes: disallow direct CAM mutation; require AD validation + explicit approval before apply.
- **[ADDED]** LLM-invented architecture: treat LLM output as candidate deltas only; validators + approval gate all structure.
- Performance on large repos: incremental hashing + scoped rg + batch indexing.
- Qdrant over-retrieval: heading-based chunking and metadata filters to constrain results.

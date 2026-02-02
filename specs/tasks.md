# Tasks: Auditable System-Understanding Diagrams

## Phase 0 — Repo cleanup + baseline
- [x] Inventory `../visitor-assistant` and define removal scope (what to delete, what to keep).
  - DoD:
    - Inventory document exists (e.g., `specs/visitor-assistant-inventory.md`) listing top-level folders/files, purpose, and any dependencies on this repo.
    - Keep/delete decisions are explicit (include any "must keep" artifacts and why).
    - Any cross-repo references (imports, docs links, scripts) are identified with exact paths.
- [x] Execute removal plan and update ignores/README to prevent reuse.
  - DoD:
    - Removal is completed exactly per the agreed scope; repo builds/runs without referencing `../visitor-assistant`.
    - `.gitignore` / tooling references are updated so the legacy project cannot be reintroduced accidentally.
    - README/docs no longer instruct users to use the legacy project; any replacement guidance is documented.
- [x] Document current repo assumptions and constraints (existing RAG, Qdrant config, logging).
  - DoD:
    - A baseline doc exists (e.g., `specs/baseline.md`) capturing what is reused vs extended vs new (with file/path pointers).
    - Key runtime deps/config are listed (Qdrant URL, collections, local folders, CLI entrypoints).
    - Known gaps/risks are recorded with mitigations and a "non-goals" section.

## Phase 1 — IR schema + validation
- [x] Define IR schema (JSON) with versioning, node/edge types, status enum, provenance rules.
  - DoD:
    - An IR schema artifact exists (JSON Schema and/or Pydantic models) with `version`, `generated_at`, `nodes`, `edges`.
    - `status` is constrained to: `implemented`, `spec_only`, `inferred`, `unknown`.
    - Provenance rules are expressible and enforceable (Markdown: file+heading+line range; Code: file+line range+symbol/callsite).
- [x] Implement IR load/save helpers and JSON schema validation.
  - DoD:
    - `app/diagram_ir/` has load/save helpers that round-trip IR without data loss.
    - A single "validate IR" function/entrypoint exists and fails with actionable error messages.
    - Unit tests cover: valid IR passes; invalid IR fails (missing required fields, invalid enums, malformed provenance).
- [x] Add validators for provenance completeness, dangling edges, status rules.
  - DoD:
    - Validators reject: missing provenance, missing line ranges, dangling node references in edges.
    - Validators enforce status rules (e.g., `unknown` edges are not emitted for compilation).
    - Tests cover at least one failing case per validator with clear expected error text.
- [x] Add deterministic IR output path config in `app/config.py`.
  - DoD:
    - `app/config.py` includes settings for IR output location (and defaults) without breaking existing config loading.
    - CLI/runtime can override the IR path via env var and/or CLI flag (documented).
    - A minimal smoke test confirms the IR file is written to the configured location.

## Phase 2 — Docs ingestion (Markdown-first)
- [ ] Implement Markdown/ticket/note collectors with explicit globs.
  - DoD:
    - Collectors scan only the intended globs: `docs/**/*.md`, `tickets/**/*.{md,txt}`, `notes/**/*.{md,txt}` (configurable).
    - Collector output includes `doc_type` + absolute/relative path normalization rules documented.
    - Tests cover: matching globs, ignoring non-matching files, stable ordering for determinism.
- [ ] Parse headings and line ranges; chunk by heading + paragraph.
  - DoD:
    - Each chunk records: `file`, `heading`, `line_start`, `line_end`, and raw text.
    - Chunk boundaries are deterministic (same input yields same chunks/line ranges).
    - Tests verify correct heading association and line-range capture on representative Markdown.
- [ ] Extend Qdrant payloads with `doc_type`, `heading`, `line_start`, `line_end`.
  - DoD:
    - Qdrant point payloads include the required fields and are queryable/filtered by them.
    - Existing chat/RAG collection behavior is unchanged (docs metadata lives in the docs collection only).
    - Integration test (can be skipped when Qdrant is absent) verifies payload fields are present after ingestion.
- [ ] Create dedicated docs collection (config + management).
  - DoD:
    - New config exists for docs collection name (e.g., `DOCS_QDRANT_COLLECTION`) separate from chat/RAG.
    - Startup/CLI ensures the docs collection exists (create-if-missing) with correct vector size/distance settings.
    - A README snippet documents how to inspect the collection and how to reset it safely.
- [ ] Add rg-based seed search for diagram-relevant chunks.
  - DoD:
    - A deterministic rg query (or small set) exists and is runnable via CLI to surface likely diagram-relevant inputs.
    - Output captures file + line numbers, and can be traced back into chunk/provenance records.
    - Tests cover parsing rg output into structured candidates (at least one Windows path + line case).

## Phase 3 — Code grounding
- [ ] Implement rg-based code search with file/line capture.
  - DoD:
    - A module/function runs rg and returns structured matches: `file`, `line`, `text` (and optionally `column`).
    - Search scope is configurable (default to `app/` and other relevant roots) and deterministic.
    - Tests cover parsing rg output and handling "no matches" cleanly.
- [ ] Add tree-sitter indexer wrapper (CLI integration, output to `out/symbols.json`).
  - DoD:
    - CLI integration exists to generate a symbol index (definitions/references/callsites where supported) into `out/symbols.json`.
    - The wrapper is optional: absence of tree-sitter tooling yields a clear warning and continues with rg-only mode.
    - A schema/contract is documented for `out/symbols.json` and validated in tests with a fixture.
- [ ] Integrate grounding outputs into IR candidate extraction.
  - DoD:
    - IR nodes/edges can be created with code provenance derived from rg/tree-sitter results.
    - Code-derived elements are tagged with status `implemented` only when grounded to actual code locations/symbols.
    - Tests cover at least one grounded node and one grounded edge from a small fixture module.

## Phase 4 — Deterministic orchestrator
- [ ] Build state machine with typed step outputs and explicit transitions.
  - DoD:
    - Orchestrator has explicit states/steps (e.g., ingest docs, index code, build IR, validate, compile diagrams).
    - Each step output is typed/validated (no unstructured dict sprawl) and serializable for persistence.
    - Determinism check: same inputs produce the same IR and diagram outputs (modulo timestamps) in tests.
- [ ] Persist state to `out/state.json` with restart support.
  - DoD:
    - State file includes `run_id`, current state, and per-step success metadata (timestamps + input hashes).
    - Re-running the CLI resumes correctly after interruption (skips completed steps when inputs unchanged).
    - Tests cover: initial run creates state; second run is a no-op when nothing changed.
- [ ] Integrate validators and repair loop triggers.
  - DoD:
    - Validation failures block diagram output and produce a repair task list with concrete missing fields/refs.
    - Repair loop is bounded and deterministic (max attempts / clear exit conditions).
    - Tests cover a failing IR that triggers repair tasks and then succeeds after applying a deterministic fix fixture.
- [ ] Ensure LLMs are stateless workers only (no workflow control).
  - DoD:
    - Orchestrator never branches on free-form LLM text; all transitions are code-driven and validator-driven.
    - Any LLM output is treated as suggestions and must pass strict parsing/validation before affecting IR.
    - Documentation explicitly states workflow control and stop conditions live in code, not the LLM.

## Phase 5 — Diagram compilation
- [ ] Implement IR -> Mermaid compiler with status-based styling.
  - DoD:
    - Compiler consumes only IR and produces valid Mermaid (unit test parses/compares expected output).
    - Edge style mapping is implemented: `implemented` solid, `spec_only` dashed, `inferred` dotted, `unknown` omitted.
    - Node/edge identifiers are sanitized consistently (no Mermaid syntax breakage).
- [ ] Implement IR -> Graphviz DOT compiler with status-based styling.
  - DoD:
    - Compiler consumes only IR and produces valid DOT with style mapping matching the spec.
    - Output is deterministic (stable ordering of nodes/edges).
    - Tests compare generated DOT against a golden output for a fixture IR.
- [ ] Enforce "IR-only" rendering (block output on validation errors).
  - DoD:
    - Compilation step refuses to run (or refuses to write output) when IR validation fails.
    - Errors are actionable: include which node/edge failed and which provenance rule was violated.
    - Test verifies invalid IR yields no diagram output artifacts.

## Phase 6 — CLI + Docker
- [ ] Add `scripts/diagram_build.py` CLI for end-to-end pipeline.
  - DoD:
    - CLI supports `--repo`, `--docs`, `--tickets`, `--notes`, `--ir`, and output locations for diagrams.
    - `--help` is accurate and includes at least one full example command.
    - End-to-end run succeeds on a small fixture set without requiring network calls (unless explicitly enabled).
- [ ] Add `docker/docker-compose.yml` to run Qdrant.
  - DoD:
    - `docker/docker-compose.yml` exists and starts Qdrant with a persistent volume and exposed port(s).
    - Docs mention how to start/stop/reset Qdrant and how to point the app at it via env vars.
    - Optional: a minimal smoke script confirms the Qdrant health endpoint is reachable after `up -d`.
- [ ] Update config and README with example commands.
  - DoD:
    - README no longer contains stale commands (e.g., `make` if no Makefile) and includes diagram pipeline usage.
    - Environment variables and defaults are documented for Qdrant + docs collection + IR paths.
    - Examples are copy/paste runnable from repo root.

## Phase 7 — Incremental updates
- [ ] Add hashing for docs/code inputs.
  - DoD:
    - Hashing covers file content + path + relevant config (so changes invalidate correctly).
    - Hash results are stored in state/cache (`out/state.json` and/or a cache file) in a stable format.
    - Tests cover: edit a file -> hash changes; unchanged files -> hash stable.
- [ ] Implement incremental re-run logic based on changed inputs.
  - DoD:
    - Orchestrator skips steps whose inputs are unchanged and whose outputs exist and validate.
    - Any changed input invalidates downstream steps deterministically (clear dependency graph).
    - Tests cover: changing a doc re-runs doc ingest + downstream; changing a code file re-runs code grounding + downstream.
- [ ] Define deterministic termination conditions.
  - DoD:
    - Termination is code-defined: "IR validates and no repair tasks pending".
    - Repair loop has explicit max attempts and produces a final failure report when exhausted.
    - Tests cover a successful termination and a bounded failure termination.

## Phase 8 — Tests
- [ ] IR validator tests (schema + provenance rules).
  - DoD:
    - Tests exist for schema validation and each provenance rule (Markdown + code).
    - `pytest` can run them locally with clear failure messages.
    - A fixture IR set is included under `tests/fixtures/` (or similar) for reuse.
- [ ] Diagram compiler tests (Mermaid/DOT output).
  - DoD:
    - Golden-file tests exist for Mermaid and DOT outputs.
    - Tests cover status styling, omission of `unknown`, and identifier sanitization.
    - Outputs are stable across runs (ordering normalized in compilers or in tests).
- [ ] Provenance extraction tests (Markdown headings + line ranges).
  - DoD:
    - Tests cover heading detection, nested headings, and paragraphs spanning multiple lines.
    - Line ranges are asserted against fixed fixtures (no off-by-one).
    - At least one Windows-style newline fixture is included to avoid platform drift.

## Phase 9 — Documentation
- [ ] Update README to remove stale `make` references or add a Makefile.
  - DoD:
    - Either (a) a working `Makefile` exists implementing the documented targets, or (b) README is updated to direct commands that exist.
    - Quick start steps are verified manually (or via a minimal script) and documented as such.
    - CI/local dev instructions are consistent with repo tooling (Python env, dependencies, etc.).
- [ ] Add usage guide for diagram pipeline (inputs, outputs, troubleshooting).
  - DoD:
    - A single guide exists (e.g., `docs/diagram_pipeline.md` or `specs/diagram_pipeline.md`) describing inputs, outputs, and folder conventions.
    - Troubleshooting covers common failures (Qdrant down, validation failures, missing tree-sitter) with fixes.
    - Guide includes a "How to verify output is auditable" checklist (provenance present, IR validated, deterministic run).


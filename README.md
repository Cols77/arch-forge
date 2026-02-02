# Auditable System-Understanding Diagrams

Build a deterministic “agentic” workflow that turns an existing codebase + docs into **auditable architecture diagrams**.

The core principle is strict authority:

- **CAM (Canonical Architecture Model)** is the only source of architectural truth.
- **Diagrams are views** compiled from CAM (never edited directly to change architecture).
- **Architecture Deltas (ADs)** are explicit, validated proposals (from chat, diagram edit events, bootstrap, or static analysis) and are **applied only with explicit approval**.

## Status

This repo is under active development. The project roadmap and acceptance criteria live in:

- `specs/highlevel_plan.md`
- `specs/plan.md`
- `specs/tasks.md`
- `specs/agentic_ai_workflow.md`

## What “auditable” means here

Every CAM node/edge is expected to carry **evidence** (e.g., file paths + line ranges, doc headings + line ranges), and outputs are intended to be **deterministic** for the same inputs (stable ordering, stable serialization).

## Development

- Run tests: `pytest`


# Baseline: current repo assumptions & constraints

As of **2026-01-31**, this repository contains an existing TourAssist-style service (FastAPI + SQLite + Qdrant-backed RAG) that will be **reused and extended** to build “Auditable System‑Understanding Diagrams”.

## What exists today (current codebase)

- **API service**: FastAPI app entrypoint at `app/main.py`.
- **Persistence**: local SQLite DB at `data/tourassist.db` (path configurable via env; initialized by `app/models/db.py`).
- **RAG**:
  - Qdrant client + collection management: `app/rag/vector_store.py`
  - Embeddings adapter w/ deterministic fallback + cache: `app/rag/embeddings.py`
  - Document ingestion (PDF/text -> paragraph-ish chunking): `app/rag/ingestion.py`
  - Retrieval helper: `app/rag/retrieval.py`
- **Observability**:
  - JSON logging formatter + configuration: `app/observability/logger.py`
  - Minimal in-process metrics store: `app/observability/metrics.py`
- **Evaluation harness**: `scripts/run_eval.py` and `app/eval/runner.py`.
- **Demo content**: `data/demo/spa.md`.

## Reuse vs extend vs new (for the diagram system)

**Reuse as-is**
- `app/rag/*` for embeddings + Qdrant access (with the important constraint that diagram docs will get a *separate* Qdrant collection later).
- `app/observability/*` for JSON logging and metrics scaffolding.
- `app/config.py` for env var loading and settings defaults.

**Extend (planned)**
- Ingestion: extend/replace current chunking in `app/rag/ingestion.py` to support deterministic Markdown heading/paragraph chunking with line-range provenance.
- Retrieval: extend `app/rag/retrieval.py` and Qdrant payload fields to return structured provenance/doc metadata (not just text).
- Config: extend `app/config.py` with diagram-specific settings (IR output path, docs collection name, docs/tickets/notes inputs).

**New (planned)**
- `app/diagram_ir/` (IR schema + validators + load/save)
- `app/docs_ingest/` (Markdown/ticket/note collectors + provenance extraction)
- `app/grounding/` (rg-based code grounding; optional tree-sitter indexer)
- `app/orchestrator/` (deterministic workflow/state machine)
- `app/diagram_compile/` (IR -> Mermaid + DOT)
- `scripts/diagram_build.py` (CLI entrypoint)
- `docker/docker-compose.yml` (Qdrant container)

## Key runtime deps & configuration

**Qdrant**
- URL: `QDRANT_URL` (default: `http://localhost:6333`) in `app/config.py`
- Collection: `QDRANT_COLLECTION` (default: `tourassist_chunks`) in `app/config.py`

**LLM / embeddings**
- Base URL: `OPENAI_BASE_URL` (default: `https://api.openai.com/v1`)
- API key: `OPENAI_API_KEY` (if unset, embeddings fall back to a deterministic SHA256-derived vector)
- Chat model: `OPENAI_CHAT_MODEL` (default: `gpt-4o-mini`)
- Embed model: `OPENAI_EMBED_MODEL` (default: `text-embedding-3-small`)
- Embed dims override: `TOURASSIST_EMBED_DIMS` (optional)

**Local paths & limits**
- Data dir: `TOURASSIST_DATA_DIR` (default: `./data`)
- DB path: `TOURASSIST_DB_PATH` (default: `<data_dir>/tourassist.db`)
- Diagram IR output: `DIAGRAM_IR_PATH` (default: `./out/ir.json`)
- Chunk size: `TOURASSIST_MAX_CHUNK_CHARS` (default: `800`)
- Retrieval: `TOURASSIST_TOP_K` (default: `4`)
- Upload limit: `TOURASSIST_MAX_FILE_SIZE_MB` (default: `10`)
- Eval timeout: `TOURASSIST_EVAL_TIMEOUT_S` (default: `20`)

**Entrypoints**
- FastAPI app: `uvicorn tourassist.app.main:app` (module path; `tourassist.app` is a thin shim over the repo’s flat `app/` folder)
- Eval runner: `python scripts/run_eval.py --tenant <id> --cases <path>`

## Known gaps/risks (and mitigations)

- **Docs provenance is missing**: current ingestion does not capture Markdown headings or line ranges; later phases add deterministic chunking + provenance validators.
- **Docs vs chat separation**: current Qdrant usage targets a single collection; later phases add a dedicated docs collection (do not change existing chat/RAG behavior).
- **README/tooling drift**: README currently references `make` targets, but no `Makefile` exists in this repo (tracked as a later doc/task update).

## Non-goals (this baseline)

- No IR schema, orchestrator, doc ingestion, or diagram compilation is implemented yet; this document is only the “starting point” inventory for phased work.

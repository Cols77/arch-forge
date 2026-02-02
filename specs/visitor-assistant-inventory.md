# Inventory: `../visitor-assistant` (legacy TourAssist repo)

As of **2026-01-31**, there is a legacy/adjacent project at `../visitor-assistant` (`C:\coding\visitor-assistant`).

This repo (`embedded_sw_coding_agent`) is the target codebase for the “Auditable System‑Understanding Diagrams” work. The adjacent `../visitor-assistant` repo appears to be an older/duplicate TourAssist implementation and is **not required** for this repo’s operation.

## Top-level inventory (what’s there)

| Path | Type | Purpose / notes |
| --- | --- | --- |
| `.git/` | dir | Separate git repository history for the legacy project. |
| `.venv/` | dir | Local Python virtual environment (not portable). |
| `app/` | dir | FastAPI service, RAG stack (Qdrant), observability, UI assets. Mirrors this repo’s `app/` structure. |
| `data/` | dir | Demo docs and local SQLite DB for TourAssist. |
| `eval/` | dir | Evaluation cases/fixtures for the TourAssist assistant. |
| `scripts/` | dir | Utility/CLI scripts (e.g., eval runner). |
| `tests/` | dir | Pytest suite for the legacy project. |
| `__pycache__/` | dir | Python bytecode cache (generated). |
| `.env` | file | Local environment variables (developer machine state). |
| `.gitignore` | file | Ignore rules for the legacy project. |
| `docker-compose.yml` | file | Container orchestration for legacy runtime dependencies. |
| `Dockerfile` | file | Container build for the legacy project. |
| `Makefile` | file | Legacy “make install/run/eval” targets. |
| `README.md` | file | Legacy quickstart docs. |
| `requirements.txt` | file | Legacy Python deps (FastAPI, Qdrant client, httpx, pypdf, pytest, dotenv). |
| `__init__.py` | file | Empty marker file (unused given the folder name contains `-`). |

## Dependencies on this repo (`embedded_sw_coding_agent`)

- No code imports, scripts, or docs in `../visitor-assistant` were found to reference this repo.
- Conversely, this repo does not import or execute code from `../visitor-assistant`.

## Cross-repo references (exact paths)

The only explicit references to `../visitor-assistant` found in this repo are in planning/spec documents:

- `specs/tasks.md` (Phase 0 cleanup items)
- `specs/plan.md` (mentions cleanup as a gap/roadmap item)

No runtime code references were found.

## Keep/delete decisions (removal scope)

**Delete**
- Delete **all contents of** `../visitor-assistant/` (the entire legacy repo, including its `.git/`, `.venv/`, and runtime artifacts).
- If Windows file locks prevent deleting the top-level directory itself, leave it empty and delete it later once handles are closed.

**Keep**
- Keep **nothing** from `../visitor-assistant` in-tree; any needed historical context is captured in this inventory document.

Rationale: `../visitor-assistant` duplicates the existing TourAssist-style code already present in this repo (which is the planned base for extension). Keeping both side-by-side increases confusion and risks accidental coupling.

## Removal status

- All contents under `../visitor-assistant/` were removed as part of Phase 0 cleanup.
- The top-level `../visitor-assistant` directory may remain present-but-empty if a Windows process holds a handle open to it; delete it later once handles are closed.

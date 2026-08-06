# Phase 1 — Repository Context Service: Verification Report

Date: 2026-08-05
Scope: `agent/` — repository understanding + semantic retrieval (no assistants, no LLM calls, no GitHub comments/issues/PRs).

## 1. Deliverables

| Deliverable | Location |
|---|---|
| Settings (additive to Phase 0) | `agent/app/core/config.py` |
| DB models (Phase 1 tables) | `agent/app/db/models.py` |
| Repositories (injected sessions) | `agent/app/db/repositories.py` |
| Alembic scaffold + initial migration | `agent/alembic.ini`, `agent/alembic/env.py`, `agent/alembic/versions/0001_initial.py` |
| Context layer | `agent/app/context/` (chunker, code/document parsers, embeddings, vector store, repository indexer, indexer pipeline, semantic search, snapshot, DI container, chunk store, application service) |
| API routes | `agent/app/api/routes/context.py` (+ `dependencies.py`, `router.py`, `main.py`) |
| Tests | `agent/tests/test_context_*.py` (10 files) |
| CI gate | `.github/workflows/agent-ci.yml` → `--cov-fail-under=95` |

## 2. Verification runs (agent venv, Python 3.12.9)

### Lint / format / types

```
ruff check app tests   -> All checks passed!
black --check app tests -> 62 files would be left unchanged.
mypy app               -> Success: no issues found in 42 source files
```

### Tests + coverage (CI flags)

```
pytest tests --tb=short --cov=app --cov-report=term-missing --cov-fail-under=95
129 passed, 2 warnings
TOTAL  1392 stmts, 60 missed -> 95.69% coverage
Required test coverage of 95% reached.
```

### Migrations

```
AGENT_DATABASE_URL=sqlite:///./_smoke_test.db alembic upgrade head
INFO [alembic.runtime.migration] Running upgrade -> 0001_initial, initial schema for the agent service
```

`agent/db/session.py::init_db()` now runs Alembic `upgrade head` (no `create_all`); startup indexing runs
after migrations only when `AGENT_INDEX_ON_STARTUP=true`.

### End-to-end smoke (unit-level, temp repo)

```
SUMMARY new_files=2 updated_files=0 removed_files=0 chunks_created=3 embeddings_created=3 took_seconds=0.06
HIT src/utils.py 1 0.607   (search "multiply calculator")
HIT README.md   3 0.305
STATUS indexed_files=2 chunk_count=3 embedding_count=3 vector_count=3 is_indexing=false
```

### Live boot (uvicorn :8077, startup indexing enabled)

```
GET  /api/context/status -> indexed_files=2, chunk_count=3, vector_count=3, is_indexing=false
POST /api/context/search {"query":"boot","limit":3} -> total=3
POST /api/context/reindex -> new_files=0 (idempotent second run)
```

## 3. Bugs found and fixed during verification

1. `ChunkRepository.upsert` looked up by autoincrement `id` instead of unique `chunk_id` → duplicate chunk
   insertion / UNIQUE constraint failure. Fixed to query by `chunk_id`.
2. Document chunks collided on `chunk_id` because section chunking re-used 0-based internal line numbers.
   Fixed with a `base_line` offset threaded through `chunk_text` so IDs/lines are document-absolute.
3. `chunk_text` produced a phantom empty chunk for files ending with `\n`; trailing empty lines are now dropped.
4. `_TS_FUNC_RE` trailing `\b` never matched arrow functions (`...=>`); removed the trailing boundary.
5. `IndexerPipeline` referenced `started` across methods (NameError); timing now passed through `_run_locked`.
6. `snapshot_provider` was invoked as a callable in `ContextService.snapshot()`; now `provider.fetch()`.

## 4. Security notes

- Sensitive path deny-list (`secrets`, `credentials`, `.env`, `*.pem`, `*.key`, `id_rsa`, …) prevents
  secret-bearing files from being indexed/embedded; covered by tests.
- `docs/architecture` and `docs/backlog` are within the default `AGENT_CONTEXT_ROOTS` but the
  sensitive-path filter still applies to any file whose path matches.
- Phase 1 makes no LLM calls and no GitHub writes; the `EmbeddingProvider`, `VectorStore`, and
  `SnapshotProvider` protocols are the seams where those integrate in Phase 2.

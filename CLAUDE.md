# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies** (requires [uv](https://docs.astral.sh/uv/getting-started/installation/)):
```bash
uv sync                  # install all deps including dev
uv sync --no-dev         # production deps only
```

**Run tests** (no external services needed — uses SQLite):
```bash
uv run pytest
uv run pytest test_blog.py::test_get_post_detail -v   # single test
```

**Lint and format** (ruff):
```bash
uv run ruff check app/ conftest.py test_blog.py        # lint
uv run ruff check --fix app/ conftest.py test_blog.py  # lint + auto-fix
uv run ruff format app/ conftest.py test_blog.py       # format
```

**Run the full stack** (API + PostgreSQL + Redis):
```bash
cp .env.example .env
docker compose up --build
```

API at `http://localhost:8000`, interactive docs at `http://localhost:8000/docs`.


## Architecture

The app lives entirely in the `app/` package. Entry point for Docker/uvicorn is `app.main:app`.

```
app/
├── main.py                        # FastAPI app, lifespan hooks (init_db + Redis)
├── core/
│   ├── config.py                  # pydantic-settings singleton (get_settings)
│   ├── database.py                # SQLAlchemy Base, lazy init_db(), get_db()
│   ├── cache.py                   # Redis client with graceful degradation
│   └── logging.py                 # configure_logging(): structlog setup
├── api/v1/
│   └── posts.py                   # Thin route handlers — HTTP concerns only
├── models/
│   └── post.py                    # ORM models: BlogPost, BlogComment
├── schemas/
│   └── post.py                    # Pydantic I/O: PostSummary, PostDetail, PaginatedResponse
├── services/
│   └── post_service.py            # Business logic + cache-aside pattern
└── repositories/
    └── post_repository.py         # All SQLAlchemy queries
```

**Request flow:** `posts.py` → `PostService` (checks Redis) → `PostRepository` (PostgreSQL) → response (written to Redis).

**Key design decisions:**

- `init_db()` is called in the FastAPI lifespan, not at import time — so tests can import `app.core.database` and override `get_db` without needing `asyncpg` installed.
- Redis is optional. If unavailable at startup, `redis_client` stays `None` and all cache calls are no-ops.
- Logging uses **structlog** (`app/core/logging.py`). `configure_logging()` is called at module level in `main.py` before the app object is created, so uvicorn and SQLAlchemy logs also pass through the structlog processor chain. Non-production → DEBUG + colored console; production → INFO + JSON. Log calls use keyword args for structured context: `logger.warning("cache_read_failed", key=key)`.
- DI wiring: `posts.py` builds `PostService(PostRepository(db))` via a `Depends` helper. Tests override `get_db` via `app.dependency_overrides`.
- Cache keys: `posts:list:p{page}:s{page_size}` and `posts:detail:{post_id}`, TTL defaults to 60s.
- Tests use SQLite (`aiosqlite`) — no Postgres needed locally.

## Dependencies

Managed with `uv`. All deps defined in `pyproject.toml`:
- **Production** — `[project.dependencies]`: fastapi, uvicorn, sqlalchemy, asyncpg, pydantic-settings, redis, alembic
- **Dev** — `[dependency-groups] dev`: pytest, pytest-asyncio, httpx, aiosqlite, ruff

## API Endpoints

- `GET /health`
- `GET /api/v1/posts?page=1&page_size=20` — paginated list with comment counts
- `GET /api/v1/posts/{post_id}` — full post with all comments

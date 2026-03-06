# Minimalist Blog API

A RESTful blog API built with **FastAPI**, **PostgreSQL**, and **Redis**. It serves blog posts with comment counts and supports pagination, with Redis caching for repeated reads.

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.115 |
| Database | PostgreSQL 16 (asyncpg + SQLAlchemy async) |
| Cache | Redis 7 (hiredis) |
| Validation | Pydantic v2 |
| Logging | structlog |
| Package manager | uv |
| Linting / formatting | Ruff |
| Testing | pytest-asyncio + SQLite (no external services) |

## Project Structure

```
app/
├── main.py                          # FastAPI app, lifespan hooks
├── api/v1/
│   ├── __init__.py                  # Aggregates all v1 routers
│   ├── health.py                    # GET /api/v1/health
│   └── posts.py                     # GET /api/v1/posts, GET /api/v1/posts/{id}
├── core/
│   ├── config.py                    # Settings (pydantic-settings, .env)
│   ├── database.py                  # Async engine, get_db() dependency
│   ├── cache.py                     # Redis init/close + get/set helpers
│   └── logging.py                   # structlog configuration
├── models/post.py                   # SQLAlchemy ORM: BlogPost, BlogComment
├── schemas/post.py                  # Pydantic response models
├── services/post_service.py         # Business logic + cache-aside
└── repositories/post_repository.py  # All SQL queries
scripts/
├── entrypoint.sh                    # Seeds DB on startup (non-production only)
└── seed.py                          # Inserts 10 posts and 6 comments
```

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (for local development)

### Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

The API will be available at `http://localhost:8000`.

On first startup the database is seeded automatically with 10 sample blog posts and 6 comments. This only runs when `APP_ENV` is not `production`.

To tear everything down including volumes:

```bash
docker compose down -v
```

### Run locally (without Docker)

```bash
uv sync                         # install all dependencies including dev
uv run uvicorn app.main:app --reload
```

You will need PostgreSQL and Redis running and a `.env` file configured (see [Configuration](#configuration)).

## API Reference

Interactive docs are available at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc`.

### Endpoints

#### `GET /api/v1/health`

Returns service health status.

```json
{ "status": "ok" }
```

---

#### `GET /api/v1/posts`

Returns a paginated list of blog posts with title and comment count. Does **not** include post body.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number (≥ 1) |
| `page_size` | integer | `20` | Items per page (1 – 100) |

**Response**
```json
{
  "items": [
    {
      "blog_post_id": 1,
      "title": "How to bake a cake",
      "published_on": "2020-02-01T00:00:00",
      "comment_count": 1
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

#### `GET /api/v1/posts/{post_id}`

Returns the full post body and all its comments. Returns `404` if the post does not exist.

```json
{
  "blog_post_id": 1,
  "title": "How to bake a cake",
  "body": "<p>Blog body</p>",
  "published_on": "2020-02-01T00:00:00",
  "comments": [
    {
      "comment_id": 6,
      "comment": "Comment body",
      "commented_on": "2020-02-21T11:46:18.147000"
    }
  ]
}
```

## Configuration

Copy `.env.example` to `.env` and adjust as needed.

```bash
# PostgreSQL
DB_USER=blog_user
DB_PASSWORD=changeme
DB_NAME=blog_db
DB_HOST=db       # use "localhost" when running outside Docker
DB_PORT=5432

# Redis
CACHE_HOST=redis       # use "localhost" when running outside Docker
CACHE_PORT=6379

# App
APP_ENV=development    # development | staging | production
LOG_LEVEL=DEBUG        # ignored in production (always INFO)
```

`APP_ENV=production` switches logging to structured JSON at INFO level and disables the automatic database seed on startup.

## Development

### Tests

Tests use an in-memory SQLite database — no running PostgreSQL or Redis required.

```bash
uv run pytest test_blog.py -v
```

### Linting and formatting

```bash
uv run ruff check app/          # check for issues
uv run ruff check --fix app/    # auto-fix where possible
uv run ruff format app/         # format code
```

VS Code users: formatting and import sorting run automatically on save via the [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) (configured in `.vscode/settings.json`).

### Hot reload

`docker compose up` mounts `./app` into the container and passes `--reload` to uvicorn. Any change to a file inside `app/` restarts the server automatically.

## Caching

The list and detail endpoints use a **cache-aside** strategy with Redis:

1. On a cache hit the response is returned immediately from Redis.
2. On a miss the result is fetched from PostgreSQL, written to Redis with a configurable TTL (default 60 s), then returned.
3. If Redis is unavailable the API degrades gracefully and reads directly from the database.

## Docker Image

The image is built in two stages:

1. **builder** — installs production dependencies via uv into a virtual environment (cached until `pyproject.toml` or `uv.lock` changes).
2. **runtime** — copies only the `.venv` and application source; no build tooling or dev dependencies are included.

The `ENTRYPOINT` runs `scripts/entrypoint.sh`, which seeds the database before handing off to `CMD` (uvicorn). The seed step is skipped when `APP_ENV=production`.

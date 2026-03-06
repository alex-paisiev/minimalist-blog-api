FROM python:3.12.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Compile .pyc files on install for faster container startup
    UV_COMPILE_BYTECODE=1 \
    # Use copy instead of hardlinks (required when venv is on a different fs than the cache)
    UV_LINK_MODE=copy

WORKDIR /app

# ── builder: install production dependencies into a virtual env ───────────────
FROM base AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies only — this layer is cached until pyproject.toml or uv.lock changes
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

# Copy application source
COPY app/ app/

# ── runtime: minimal image — no uv, no build tooling, no dev deps ─────────────
FROM base AS runtime

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY scripts/ scripts/

RUN chmod +x scripts/entrypoint.sh

# Activate the virtual env by prepending it to PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

ENTRYPOINT ["scripts/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

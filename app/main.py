from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health_check import router as health_router
from app.api.v1 import router as v1_router
from app.core.cache import close_redis, init_redis
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import configure_logging

settings = get_settings()

# Configure logging before the app object is created so that all subsequent
# log calls — including those from FastAPI/uvicorn — use the structured format.
configure_logging(settings.APP_ENV, settings.LOG_LEVEL)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("startup", app_env=settings.APP_ENV)
    init_db()
    await init_redis()
    yield
    logger.info("shutdown")
    await close_redis()


app = FastAPI(
    title="ALM Blog API",
    description="A minimalist blog API built with FastAPI, PostgreSQL, and Redis.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/health-check")
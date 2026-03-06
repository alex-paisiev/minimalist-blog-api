import logging
import sys
from typing import Any

import structlog


def configure_logging(app_env: str, log_level: str) -> None:
    """Configure structlog with stdlib integration.

    - Non-production: DEBUG level, human-readable colored console output.
    - Production:     INFO level, JSON output suited for log aggregators.

    Stdlib integration means third-party loggers (uvicorn, SQLAlchemy, etc.)
    are also routed through structlog's processor chain for consistent output.
    """
    # Production always uses INFO; other envs use the configured level
    level = (
        logging.INFO
        if app_env == "production"
        else getattr(logging, log_level.upper(), logging.DEBUG)
    )

    # Processors applied to every log record (structlog-native and stdlib foreign)
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if app_env == "production"
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    # Configure structlog itself
    structlog.configure(
        processors=shared_processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

    # Wire up stdlib logging so uvicorn/SQLAlchemy logs pass through structlog too
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

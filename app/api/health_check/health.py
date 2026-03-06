from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import redis_client
from app.core.database import get_db
from app.schemas.health_check import HealthCheckResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/",
    summary="Health Check",
    description="Reports connectivity status for the API, database, and Redis cache.",
    response_model=HealthCheckResponse,
)
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> HealthCheckResponse:
    services: dict[str, str] = {}

    try:
        await db.execute(text("SELECT 1"))
        services["database"] = "ok"
    except Exception:
        services["database"] = "unavailable"

    try:
        if redis_client is None:
            raise RuntimeError
        await redis_client.ping()
        services["redis"] = "ok"
    except Exception:
        services["redis"] = "unavailable"

    if services["database"] == "unavailable":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall = "unhealthy"
    elif services["redis"] == "unavailable":
        overall = "degraded"
    else:
        overall = "ok"

    return HealthCheckResponse(status=overall, services=services)

from fastapi import APIRouter

from app.api.health_check import health

router = APIRouter()

router.include_router(health.router)
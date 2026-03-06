from fastapi import APIRouter

from app.api.v1 import posts

router = APIRouter()

router.include_router(posts.router)

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.repositories.post_repository import PostRepository
from app.schemas.post import PaginatedResponse, PostDetail
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["Blog Posts"])
settings = get_settings()


def _get_post_service(db: AsyncSession = Depends(get_db)) -> PostService:
    return PostService(PostRepository(db))


PostServiceDep = Annotated[PostService, Depends(_get_post_service)]


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List all blog posts",
    description=(
        "Returns a paginated list of blog post titles with their comment counts, "
        "ordered by most recently published."
    ),
)
async def list_posts(
    service: PostServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Items per page",
    ),
) -> PaginatedResponse:
    items = await service.list_posts(page, page_size)
    total = await service.get_total_posts()
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{post_id}",
    response_model=PostDetail,
    summary="Get a blog post",
    description="Returns the full blog post body along with all of its comments.",
)
async def get_post(
    post_id: int,
    service: PostServiceDep,
) -> PostDetail:
    
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blog post {post_id} not found",
            )
    return post

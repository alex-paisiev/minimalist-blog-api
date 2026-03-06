import logging

from fastapi import HTTPException, status

from app.core.cache import cache_get, cache_set
from app.repositories.post_repository import PostRepository
from app.schemas.post import PostDetail, PostSummary

logger = logging.getLogger(__name__)


class PostService:
    """Business logic for blog post operations with cache-aside pattern."""
    
    def __init__(self, repo: PostRepository) -> None:
        logger.info("Initializing PostService with PostRepository")
        self._repo = repo

    async def get_total_posts(self) -> int:
        """Get total number of posts, used for pagination metadata."""
        total = await self._repo.count_posts()
        return total
    
    async def list_posts(self, page: int, page_size: int) -> list[PostSummary]:
        cache_key = f"posts:list:p{page}:s{page_size}"
        items = await cache_get(cache_key)
        if items:
            return items

        items = await self._repo.get_posts_with_comment_count(page, page_size)
        await cache_set(cache_key, items)
        return items
    

    async def get_post(self, post_id: int) -> PostDetail | None:
        cache_key = f"posts:detail:{post_id}"
        cached = await cache_get(cache_key)
        if cached:
            return PostDetail(**cached)

        post = await self._repo.get_post_by_id(post_id)
        if not post:
            return None

        detail = PostDetail.model_validate(post)
        await cache_set(cache_key, detail.model_dump())
        return detail

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.post import BlogComment, BlogPost
from app.schemas.post import PostSummary

logger = logging.getLogger(__name__)

class PostRepository:
    """Encapsulates all blog post database operations."""

    def __init__(self, db: AsyncSession) -> None:
        logger.info("Initializing PostRepository with AsyncSession")
        self._db = db

    async def get_posts_with_comment_count(
        self, page: int, page_size: int
    ) -> list[PostSummary]:
        """Return paginated post summaries with comment counts."""

        stmt = (
            select(
                BlogPost.blog_post_id,
                BlogPost.title,
                BlogPost.published_on,
                func.count(BlogComment.comment_id).label("comment_count"),
            )
            .outerjoin(BlogComment, BlogPost.blog_post_id == BlogComment.blog_post_id)
            .group_by(BlogPost.blog_post_id)
            .order_by(BlogPost.published_on.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        rows = (await self._db.execute(stmt)).all()
        items = [PostSummary.model_validate(row._mapping) for row in rows]
        return items
        
    async def count_posts(self) -> int:
        """Return total number of blog posts."""
        stmt = select(func.count(BlogPost.blog_post_id))
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def get_post_by_id(self, post_id: int) -> BlogPost | None:
        """Return a single post with its comments eagerly loaded."""
        stmt = (
            select(BlogPost)
            .options(selectinload(BlogPost.comments))
            .where(BlogPost.blog_post_id == post_id)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

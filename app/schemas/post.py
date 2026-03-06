from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------- Comments ----------
class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comment_id: int
    comment: str
    commented_on: datetime


# ---------- Blog Posts ----------
class PostSummary(BaseModel):
    """List-view: title + comment count."""

    model_config = ConfigDict(from_attributes=True)

    blog_post_id: int
    title: str
    published_on: datetime
    comment_count: int

# ---------- Post Details ----------
class PostDetail(BaseModel):
    """Detail-view: full post with comments."""

    model_config = ConfigDict(from_attributes=True)

    blog_post_id: int
    title: str
    body: str
    published_on: datetime
    comments: list[CommentOut]


# ---------- Pagination ----------
class PaginatedResponse(BaseModel):
    """Generic paginated wrapper."""

    items: list[PostSummary]
    total: int
    page: int
    page_size: int
    total_pages: int

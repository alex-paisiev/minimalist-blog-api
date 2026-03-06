from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BlogPost(Base):
    __tablename__ = "blog_posts"

    blog_post_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    published_on: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    comments: Mapped[list["BlogComment"]] = relationship(
        back_populates="post", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<BlogPost(id={self.blog_post_id}, title='{self.title}')>"


class BlogComment(Base):
    __tablename__ = "blog_comment"

    comment_id: Mapped[int] = mapped_column(primary_key=True)
    blog_post_id: Mapped[int] = mapped_column(
        ForeignKey("blog_posts.blog_post_id"), nullable=False, index=True
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    commented_on: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    post: Mapped["BlogPost"] = relationship(back_populates="comments")

    def __repr__(self) -> str:
        return f"<BlogComment(id={self.comment_id}, post_id={self.blog_post_id})>"

#!/usr/bin/env python3
"""Seed the database with sample blog posts and comments.

Called by entrypoint.sh on container startup in non-production environments.
Uses INSERT ... ON CONFLICT DO NOTHING so it is safe to run multiple times.
Retries the DB connection to handle the brief window after the healthcheck passes.
"""

import asyncio
import os
import sys
from datetime import datetime

import asyncpg

DSN = (
    f"postgresql://{os.getenv('DB_USER', 'blog_user')}"
    f":{os.getenv('DB_PASSWORD', 'blog_password')}"
    f"@{os.getenv('DB_HOST', 'db')}"
    f":{os.getenv('DB_PORT', '5432')}"
    f"/{os.getenv('DB_NAME', 'blog_db')}"
)


def dt(value: str) -> datetime:
    """Parse a date or datetime string into a datetime object."""
    fmt = "%Y-%m-%d %H:%M:%S.%f" if " " in value else "%Y-%m-%d"
    return datetime.strptime(value, fmt)


POSTS = [
    (1, "How to bake a cake", "<p>Blog body</p>", dt("2020-02-01")),
    (2, "How to bake cookies", "<p>Blog body</p>", dt("2020-02-14")),
    (3, "How to bake bread", "<p>Blog body</p>", dt("2020-02-25")),
    (4, "How to make custard", "<p>Blog body</p>", dt("2020-03-10")),
    (5, "The joys of raisins", "<p>Blog body</p>", dt("2020-03-16")),
    (6, "Making pizza dough", "<p>Blog body</p>", dt("2020-03-28")),
    (
        7,
        "To kneed, or not to kneed, that is the question",
        "<p>Blog body</p>",
        dt("2020-04-04"),
    ),
    (8, "Is Bake Off better on Channel 4?", "<p>Blog body</p>", dt("2020-04-21")),
    (9, "The perfect Victoria Sponge", "<p>Blog body</p>", dt("2020-03-01")),
    (10, "How to make a croissant", "<p>Blog body</p>", dt("2020-02-01")),
]

COMMENTS = [
    (1, 2, "These are great cookies.", dt("2020-02-14 18:42:44.158")),
    (2, 6, "Fairly average dough.", dt("2020-04-08 11:56:21.136")),
    (3, 2, "Yummy cookies.", dt("2020-03-08 10:25:35.215")),
    (4, 4, "My custard was lumpy.", dt("2020-04-08 08:56:12.109")),
    (5, 7, "Comment body", dt("2020-05-10 11:21:08.112")),
    (6, 1, "Comment body", dt("2020-02-21 11:46:18.147")),
]


async def connect_with_retry(
    retries: int = 10, delay: float = 2.0
) -> asyncpg.Connection:
    for attempt in range(1, retries + 1):
        try:
            return await asyncpg.connect(DSN)
        except (asyncpg.PostgresError, OSError) as exc:
            if attempt == retries:
                print(
                    f"[seed] Could not connect to database after {retries} attempts: {exc}",
                    flush=True,
                )
                sys.exit(1)
            print(
                f"[seed] Waiting for database (attempt {attempt}/{retries})...",
                flush=True,
            )
            await asyncio.sleep(delay)


async def seed() -> None:
    conn = await connect_with_retry()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                blog_post_id SERIAL PRIMARY KEY,
                title        VARCHAR(255) NOT NULL,
                body         TEXT NOT NULL,
                published_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_comment (
                comment_id   SERIAL PRIMARY KEY,
                blog_post_id INTEGER NOT NULL,
                comment      TEXT NOT NULL,
                commented_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_blog_comment_blog_post
                    FOREIGN KEY (blog_post_id) REFERENCES blog_posts(blog_post_id)
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_blog_comment_post_id
                ON blog_comment(blog_post_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_blog_posts_published_on
                ON blog_posts(published_on DESC)
        """)

        await conn.executemany(
            """
            INSERT INTO blog_posts (blog_post_id, title, body, published_on)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (blog_post_id) DO NOTHING
            """,
            POSTS,
        )
        await conn.execute(
            "SELECT setval('blog_posts_blog_post_id_seq',"
            " (SELECT MAX(blog_post_id) FROM blog_posts))"
        )

        await conn.executemany(
            """
            INSERT INTO blog_comment (comment_id, blog_post_id, comment, commented_on)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (comment_id) DO NOTHING
            """,
            COMMENTS,
        )
        await conn.execute(
            "SELECT setval('blog_comment_comment_id_seq',"
            " (SELECT MAX(comment_id) FROM blog_comment))"
        )

        print(
            f"[seed] Done — {len(POSTS)} posts, {len(COMMENTS)} comments seeded.",
            flush=True,
        )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())

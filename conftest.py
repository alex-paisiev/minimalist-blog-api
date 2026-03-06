import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.core.database import Base, get_db
from app.main import app
from app.models.post import BlogComment, BlogPost

# Use SQLite for tests — no external DB needed
TEST_DB_URL = "sqlite+aiosqlite:///test.db"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def seeded_db(db_session: AsyncSession):
    """Insert test data."""
    posts = [
        BlogPost(blog_post_id=1, title="First Post", body="<p>Body 1</p>"),
        BlogPost(blog_post_id=2, title="Second Post", body="<p>Body 2</p>"),
    ]
    db_session.add_all(posts)
    await db_session.flush()

    comments = [
        BlogComment(comment_id=1, blog_post_id=1, comment="Great post!"),
        BlogComment(comment_id=2, blog_post_id=1, comment="Thanks for sharing."),
        BlogComment(comment_id=3, blog_post_id=2, comment="Nice."),
    ]
    db_session.add_all(comments)
    await db_session.commit()
    return db_session


@pytest_asyncio.fixture
async def client(seeded_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client wired to the test database."""

    async def _override_db():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = _override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

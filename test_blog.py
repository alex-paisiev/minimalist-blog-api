import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/api/health-check/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")  # Redis may be unavailable in tests
    assert data["services"]["database"] == "ok"
    assert "redis" in data["services"]


@pytest.mark.asyncio
async def test_list_posts_returns_summaries(client: AsyncClient):
    resp = await client.get("/api/v1/posts")
    assert resp.status_code == 200

    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Each item should have title and comment_count
    for item in data["items"]:
        assert "title" in item
        assert "comment_count" in item
        assert "body" not in item  # list view should NOT include body


@pytest.mark.asyncio
async def test_list_posts_comment_counts(client: AsyncClient):
    resp = await client.get("/api/v1/posts")
    items = {i["blog_post_id"]: i for i in resp.json()["items"]}

    assert items[1]["comment_count"] == 2  # First Post has 2 comments
    assert items[2]["comment_count"] == 1  # Second Post has 1 comment


@pytest.mark.asyncio
async def test_list_posts_pagination(client: AsyncClient):
    resp = await client.get("/api/v1/posts?page=1&page_size=1")
    data = resp.json()

    assert len(data["items"]) == 1
    assert data["total"] == 2
    assert data["total_pages"] == 2
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_get_post_detail(client: AsyncClient):
    resp = await client.get("/api/v1/posts/1")
    assert resp.status_code == 200

    data = resp.json()
    assert data["title"] == "First Post"
    assert data["body"] == "<p>Body 1</p>"
    assert len(data["comments"]) == 2


@pytest.mark.asyncio
async def test_get_post_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/posts/999")
    assert resp.status_code == 404

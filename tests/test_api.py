import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from personaforge.backend.app.main import app
from personaforge.backend.app.database.connection import init_db, engine
from sqlmodel import SQLModel

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    await init_db()
    yield

@pytest.mark.asyncio
async def test_get_stats():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_runs" in data
    assert "total_conversations" in data

@pytest.mark.asyncio
async def test_get_runs():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_failures():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/failures")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_agent_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/agent-health")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_persona_performance():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/persona-performance")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


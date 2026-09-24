from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.redis import reset_redis_client
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import User, UserPreferences
from app.db.session import get_db
from app.main import create_app

TEST_DB_URL = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"

engine = create_async_engine(
    TEST_DB_URL, poolclass=StaticPool, connect_args={"check_same_thread": False}
)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as s:
        yield s


@pytest_asyncio.fixture
async def db_session():
    reset_redis_client()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as s:
        from app.db.seed import seed_all

        await seed_all(s)
        yield s


@pytest_asyncio.fixture
async def client(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client, db_session):
    email = f"user-{uuid.uuid4().hex[:8]}@test.ru"
    password = "password123"
    user = User(email=email, hashed_password=get_password_hash(password), display_name="Test")
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserPreferences(user_id=user.id))
    await db_session.commit()
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

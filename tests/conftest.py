import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

import models  # noqa: F401  (registers the Sale table on Base.metadata)
from main import app
from database import Base, get_session


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "test_sales.db"
    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file.as_posix()}", poolclass=NullPool
    )
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async def create_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(create_tables())

    async def override_get_session():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)

    app.dependency_overrides.clear()
    asyncio.run(test_engine.dispose())
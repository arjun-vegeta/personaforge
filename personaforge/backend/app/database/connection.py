import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlalchemy.pool import NullPool

# Default to SQLite for local development if Postgres not configured
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./personaforge.db")

# Need to handle sqlite specifically for concurrency/typing if needed, but for POC it's fine
if "pytest" in sys.modules:
    engine = create_async_engine(DATABASE_URL, echo=True, poolclass=NullPool)
else:
    engine = create_async_engine(DATABASE_URL, echo=True)


async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

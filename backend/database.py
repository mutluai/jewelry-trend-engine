from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from supabase import create_client, Client
from config import get_settings

settings = get_settings()

# SQLAlchemy async engine
engine = create_async_engine(
    settings.database_url,
    echo=not settings.is_production,
    poolclass=NullPool,  # Railway/Supabase: use NullPool for serverless compatibility
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_supabase_client() -> Client:
    """Service role client — only use in backend, never expose to frontend."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_supabase_anon_client() -> Client:
    """Anon client — safe for read-only dashboard use."""
    return create_client(settings.supabase_url, settings.supabase_anon_key)

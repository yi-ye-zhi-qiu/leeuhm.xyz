"""Database connector for FastAPI & extracty."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


from config import settings

engine = create_async_engine(settings.db_url)

# With "def" in FastAPI, routes run in a different thread pool which prevents
# the function from blocking the main event loop. With "async def", FastAPI
# runs directly in the event loop.

# Async session factory.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    # Prevent lazy-loading.
    expire_on_commit=False,
)


# An async generator dependency function for database sessions.
async def db():
    async with AsyncSessionLocal() as db:
        yield db

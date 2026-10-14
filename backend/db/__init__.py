from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


from ..config import settings

engine = create_async_engine(settings.db_url)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def db():
    async with AsyncSessionLocal() as db:
        yield db


async def execute_statement(statement: str):
    async with engine.connect() as connection:
        result = connection.execute(text(statement))
        return result

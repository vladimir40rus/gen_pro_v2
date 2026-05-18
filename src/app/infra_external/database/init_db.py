import logging
from sqlalchemy.ext.asyncio import AsyncEngine
from app.infra_external.models.base import Base

logger = logging.getLogger(__name__)


async def create_tables(engine: AsyncEngine):
    """Создание всех таблиц в базе данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Tables created successfully")


async def drop_tables(engine: AsyncEngine):
    """Удаление всех таблиц из базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("❌ Tables dropped successfully")


async def reset_tables(engine: AsyncEngine):
    """Сброс базы данных (удаление и создание заново)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("🔄 Database reset successfully")
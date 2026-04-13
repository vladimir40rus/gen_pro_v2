import asyncio
from app.database import engine, Base
import app.models  # Импортируем модели

async def create_tables():
    """Создает таблицы в базе данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created!")

async def drop_tables():
    """⚠️ Удаляет все таблицы (осторожно!)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("❌ Database tables dropped!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        asyncio.run(drop_tables())
    else:
        asyncio.run(create_tables())
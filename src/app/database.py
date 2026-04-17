from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import os

# Создание базового класса для моделей
Base = declarative_base()

# Настройка подключения к PostgreSQL из переменной окружения
# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "postgresql+asyncpg://postgres:postgres@db:5432/fastapi_db"  # Значение по умолчанию
# )
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/fastapi_db"  # Значение по умолчанию
)
# Создание engine (только один раз!)
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Выводить SQL-запросы (полезно для отладки)
    pool_size=5,
    max_overflow=10
)

# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Асинхронная функция для получения сессии
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
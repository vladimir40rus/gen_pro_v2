from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

# Подключаемся к PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=True)

# Фабрика сессий
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)

# Базовый класс для таблиц
Base = declarative_base()

# Функция для получения сессии БД
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
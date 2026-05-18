from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.infra_external.models import FavoriteDB


class FavoriteRepo:
    """Репозиторий для работы с избранным в БД"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add(self, user_id: int, article_id: int) -> None:
        """Добавить статью в избранное"""
        existing = await self.exists(user_id, article_id)
        if existing:
            return

        favorite = FavoriteDB(user_id=user_id, article_id=article_id)
        self.db_session.add(favorite)
        await self.db_session.commit()

    async def remove(self, user_id: int, article_id: int) -> None:
        """Удалить статью из избранного"""
        result = await self.db_session.execute(
            select(FavoriteDB).where(
                FavoriteDB.user_id == user_id,
                FavoriteDB.article_id == article_id
            )
        )
        favorite = result.scalar_one_or_none()
        if favorite:
            await self.db_session.delete(favorite)
            await self.db_session.commit()

    async def exists(self, user_id: int, article_id: int) -> bool:
        """Проверить, находится ли статья в избранном"""
        result = await self.db_session.execute(
            select(FavoriteDB).where(
                FavoriteDB.user_id == user_id,
                FavoriteDB.article_id == article_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_favorites_count(self, article_id: int) -> int:
        """Получить количество избранных для статьи"""
        result = await self.db_session.execute(
            select(func.count()).select_from(FavoriteDB).where(FavoriteDB.article_id == article_id)
        )
        return result.scalar() or 0


async def get_favorite_repo(db_session: AsyncSession) -> FavoriteRepo:
    """Dependency для получения FavoriteRepo"""
    return FavoriteRepo(db_session)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.infra_external.models import FollowerDB


class FollowerRepo:
    """Репозиторий для работы с подписками в БД"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def follow(self, follower_id: int, following_id: int) -> None:
        """Подписаться на пользователя"""
        if follower_id == following_id:
            raise ValueError("Cannot follow yourself")

        existing = await self.is_following(follower_id, following_id)
        if existing:
            return

        follow = FollowerDB(follower_id=follower_id, following_id=following_id)
        self.db_session.add(follow)
        await self.db_session.commit()

    async def unfollow(self, follower_id: int, following_id: int) -> None:
        """Отписаться от пользователя"""
        result = await self.db_session.execute(
            select(FollowerDB).where(
                FollowerDB.follower_id == follower_id,
                FollowerDB.following_id == following_id
            )
        )
        follow = result.scalar_one_or_none()
        if follow:
            await self.db_session.delete(follow)
            await self.db_session.commit()

    async def is_following(self, follower_id: int, following_id: int) -> bool:
        """Проверить, подписан ли пользователь"""
        result = await self.db_session.execute(
            select(FollowerDB).where(
                FollowerDB.follower_id == follower_id,
                FollowerDB.following_id == following_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_followers_count(self, user_id: int) -> int:
        """Получить количество подписчиков"""
        result = await self.db_session.execute(
            select(func.count()).select_from(FollowerDB).where(FollowerDB.following_id == user_id)
        )
        return result.scalar() or 0

    async def get_following_count(self, user_id: int) -> int:
        """Получить количество подписок"""
        result = await self.db_session.execute(
            select(func.count()).select_from(FollowerDB).where(FollowerDB.follower_id == user_id)
        )
        return result.scalar() or 0


async def get_follower_repo(db_session: AsyncSession) -> FollowerRepo:
    """Dependency для получения FollowerRepo"""
    return FollowerRepo(db_session)
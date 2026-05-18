from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.infra_external.models import UserDB


class UserRepo:
    """Репозиторий для работы с пользователями в БД"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, user_id: int) -> Optional[UserDB]:
        """Получить пользователя по ID"""
        result = await self.db_session.execute(
            select(UserDB).where(UserDB.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[UserDB]:
        """Получить пользователя по username"""
        result = await self.db_session.execute(
            select(UserDB).where(UserDB.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[UserDB]:
        """Получить пользователя по email"""
        result = await self.db_session.execute(
            select(UserDB).where(UserDB.email == email)
        )
        return result.scalar_one_or_none()

    async def get_current_user(self) -> Optional[UserDB]:
        """Получить первого пользователя (временно, пока нет JWT)"""
        result = await self.db_session.execute(
            select(UserDB).order_by(UserDB.id).limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, username: str, email: str, password_hash: str,
                     bio: str = None, image_url: str = None) -> UserDB:
        """Создать нового пользователя"""
        user = UserDB(
            username=username,
            email=email,
            password_hash=password_hash,
            bio=bio,
            image_url=image_url
        )
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def update(self, user: UserDB) -> UserDB:
        """Обновить пользователя"""
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def delete(self, user: UserDB) -> None:
        """Удалить пользователя"""
        await self.db_session.delete(user)
        await self.db_session.commit()

    async def get_stats(self, user_id: int) -> dict:
        """Получить статистику пользователя"""
        from app.infra_external.models import ArticleDB, CommentDB, FavoriteDB, FollowerDB

        # Количество статей
        articles_result = await self.db_session.execute(
            select(func.count()).select_from(ArticleDB).where(ArticleDB.author_id == user_id)
        )
        articles_count = articles_result.scalar() or 0

        # Количество комментариев
        comments_result = await self.db_session.execute(
            select(func.count()).select_from(CommentDB).where(CommentDB.author_id == user_id)
        )
        comments_count = comments_result.scalar() or 0

        # Количество подписчиков
        followers_result = await self.db_session.execute(
            select(func.count()).select_from(FollowerDB).where(FollowerDB.following_id == user_id)
        )
        followers_count = followers_result.scalar() or 0

        # Количество подписок
        following_result = await self.db_session.execute(
            select(func.count()).select_from(FollowerDB).where(FollowerDB.follower_id == user_id)
        )
        following_count = following_result.scalar() or 0

        return {
            "articles_count": articles_count,
            "comments_count": comments_count,
            "followers_count": followers_count,
            "following_count": following_count
        }


async def get_user_repo(db_session: AsyncSession) -> UserRepo:
    """Dependency для получения UserRepo"""
    return UserRepo(db_session)
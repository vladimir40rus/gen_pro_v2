from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple

from app.infra_external.models import ArticleDB, UserDB, TagDB, FavoriteDB, article_tag_association


class ArticleRepo:
    """Репозиторий для работы со статьями в БД"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_slug(self, slug: str) -> Optional[ArticleDB]:
        """Получить статью по slug"""
        result = await self.db_session.execute(
            select(ArticleDB).where(ArticleDB.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, article_id: int) -> Optional[ArticleDB]:
        """Получить статью по ID"""
        result = await self.db_session.execute(
            select(ArticleDB).where(ArticleDB.id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_list(
            self,
            skip: int = 0,
            limit: int = 20,
            tag: Optional[str] = None,
            author: Optional[str] = None,
            favorited: Optional[str] = None
    ) -> Tuple[List[ArticleDB], int]:
        """Получить список статей с фильтрацией и пагинацией"""

        query = select(ArticleDB)

        # Фильтр по автору
        if author:
            author_result = await self.db_session.execute(
                select(UserDB).where(UserDB.username == author)
            )
            author_user = author_result.scalar_one_or_none()
            if author_user:
                query = query.where(ArticleDB.author_id == author_user.id)
            else:
                return [], 0

        # Фильтр по тегу
        if tag:
            tag_result = await self.db_session.execute(
                select(TagDB).where(TagDB.name == tag)
            )
            tag_obj = tag_result.scalar_one_or_none()
            if tag_obj:
                query = query.join(article_tag_association).where(
                    article_tag_association.c.tag_id == tag_obj.id
                )

        # Фильтр по избранному
        if favorited:
            user_result = await self.db_session.execute(
                select(UserDB).where(UserDB.username == favorited)
            )
            user = user_result.scalar_one_or_none()
            if user:
                query = query.join(FavoriteDB).where(FavoriteDB.user_id == user.id)

        # Подсчёт общего количества
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db_session.execute(count_query)
        total = total_result.scalar() or 0

        # Пагинация
        query = query.order_by(desc(ArticleDB.created_at)).offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        articles = result.scalars().all()

        return articles, total

    async def create(self, article: ArticleDB) -> ArticleDB:
        """Создать статью"""
        self.db_session.add(article)
        await self.db_session.commit()
        await self.db_session.refresh(article)
        return article

    async def update(self, article: ArticleDB) -> ArticleDB:
        """Обновить статью"""
        await self.db_session.commit()
        await self.db_session.refresh(article)
        return article

    async def delete(self, article: ArticleDB) -> None:
        """Удалить статью"""
        await self.db_session.delete(article)
        await self.db_session.commit()

    async def get_feed(self, user_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[ArticleDB], int]:
        """Получить ленту статей (от авторов, на которых подписан пользователь)"""
        from app.infra_external.models import FollowerDB

        # Получаем ID авторов, на которых подписан пользователь
        following_result = await self.db_session.execute(
            select(FollowerDB.following_id).where(FollowerDB.follower_id == user_id)
        )
        following_ids = [row[0] for row in following_result.all()]

        if not following_ids:
            return [], 0

        query = select(ArticleDB).where(ArticleDB.author_id.in_(following_ids))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db_session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(desc(ArticleDB.created_at)).offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        articles = result.scalars().all()

        return articles, total


async def get_article_repo(db_session: AsyncSession) -> ArticleRepo:
    """Dependency для получения ArticleRepo"""
    return ArticleRepo(db_session)
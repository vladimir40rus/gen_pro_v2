from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.infra_external.models import CommentDB


class CommentRepo:
    """Репозиторий для работы с комментариями в БД"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, comment_id: int) -> Optional[CommentDB]:
        """Получить комментарий по ID"""
        result = await self.db_session.execute(
            select(CommentDB).where(CommentDB.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_article(self, article_id: int, skip: int = 0, limit: int = 20) -> List[CommentDB]:
        """Получить комментарии к статье"""
        result = await self.db_session.execute(
            select(CommentDB)
            .where(CommentDB.article_id == article_id)
            .order_by(desc(CommentDB.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, body: str, article_id: int, author_id: int) -> CommentDB:
        """Создать комментарий"""
        comment = CommentDB(
            body=body,
            article_id=article_id,
            author_id=author_id
        )
        self.db_session.add(comment)
        await self.db_session.commit()
        await self.db_session.refresh(comment)
        return comment

    async def update(self, comment: CommentDB) -> CommentDB:
        """Обновить комментарий"""
        await self.db_session.commit()
        await self.db_session.refresh(comment)
        return comment

    async def delete(self, comment: CommentDB) -> None:
        """Удалить комментарий"""
        await self.db_session.delete(comment)
        await self.db_session.commit()

    async def get_comments_count(self, article_id: int) -> int:
        """Получить количество комментариев для статьи"""
        result = await self.db_session.execute(
            select(func.count()).select_from(CommentDB).where(CommentDB.article_id == article_id)
        )
        return result.scalar() or 0


async def get_comment_repo(db_session: AsyncSession) -> CommentRepo:
    """Dependency для получения CommentRepo"""
    return CommentRepo(db_session)
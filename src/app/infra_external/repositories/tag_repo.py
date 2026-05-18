from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Tuple, Optional

from app.infra_external.models import TagDB, article_tag_association


class TagRepo:
    """Репозиторий для работы с тегами в БД"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_all(self) -> List[str]:
        """Получить все теги (только названия)"""
        result = await self.db_session.execute(
            select(TagDB.name).order_by(TagDB.name)
        )
        return [row[0] for row in result.all()]

    async def get_by_name(self, name: str) -> Optional[TagDB]:
        """Получить тег по имени"""
        result = await self.db_session.execute(
            select(TagDB).where(TagDB.name == name)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, name: str) -> TagDB:
        """Получить тег или создать новый"""
        tag = await self.get_by_name(name)
        if not tag:
            tag = TagDB(name=name)
            self.db_session.add(tag)
            await self.db_session.commit()
            await self.db_session.refresh(tag)
        return tag

    async def get_popular(self, min_count: int = 5) -> List[Tuple[str, int]]:
        """Получить популярные теги с количеством статей"""
        query = (
            select(TagDB.name, func.count(article_tag_association.c.article_id).label('count'))
            .join(article_tag_association, TagDB.id == article_tag_association.c.tag_id)
            .group_by(TagDB.id)
            .having(func.count(article_tag_association.c.article_id) >= min_count)
            .order_by(func.count(article_tag_association.c.article_id).desc())
        )
        result = await self.db_session.execute(query)
        return [(row[0], row[1]) for row in result.all()]

    async def add_tag_to_article(self, article_id: int, tag_id: int) -> None:
        """Добавить тег к статье"""
        # Проверяем, не добавлен ли уже
        result = await self.db_session.execute(
            select(article_tag_association).where(
                article_tag_association.c.article_id == article_id,
                article_tag_association.c.tag_id == tag_id
            )
        )
        if result.first():
            return

        # Добавляем связь
        await self.db_session.execute(
            article_tag_association.insert().values(
                article_id=article_id,
                tag_id=tag_id
            )
        )
        await self.db_session.commit()

    async def get_tags_for_article(self, article_id: int) -> List[str]:
        """Получить все теги статьи"""
        query = (
            select(TagDB.name)
            .join(article_tag_association, TagDB.id == article_tag_association.c.tag_id)
            .where(article_tag_association.c.article_id == article_id)
            .order_by(TagDB.name)
        )
        result = await self.db_session.execute(query)
        return [row[0] for row in result.all()]


async def get_tag_repo(db_session: AsyncSession) -> TagRepo:
    """Dependency для получения TagRepo"""
    return TagRepo(db_session)
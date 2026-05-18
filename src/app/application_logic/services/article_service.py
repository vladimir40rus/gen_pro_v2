from datetime import datetime
from typing import Optional, List, Tuple

from app.domain.entity.article import Article
from app.application_logic.dto.article_dto import (
    ArticleCreateDTO, ArticleUpdateDTO, ArticleResponseDTO, AuthorDTO
)
from app.infra_external.repositories.article_repo import ArticleRepo
from app.infra_external.repositories.user_repo import UserRepo
from app.infra_external.repositories.tag_repo import TagRepo
from app.infra_external.models import ArticleDB, TagDB, FavoriteDB, CommentDB


class ArticleService:
    """Сервис для работы со статьями"""

    def __init__(self, article_repo: ArticleRepo, user_repo: UserRepo, tag_repo: TagRepo):
        self.article_repo = article_repo
        self.user_repo = user_repo
        self.tag_repo = tag_repo

    async def _get_author_dto(self, author_id: int, current_user_id: Optional[int] = None) -> AuthorDTO:
        """Получить DTO автора"""
        author_db = await self.user_repo.get_by_id(author_id)

        # Получение статистики автора
        stats = await self.user_repo.get_stats(author_id)

        # Проверка подписки текущего пользователя
        following = False
        if current_user_id:
            from app.infra_external.models import FollowerDB
            # TODO: проверить подписку

        return AuthorDTO(
            username=author_db.username,
            bio=author_db.bio,
            image_url=author_db.image_url,
            following=following,
            followers_count=stats["followers_count"],
            following_count=stats["following_count"],
            articles_count=stats["articles_count"]
        )

    async def _get_tags_for_article(self, article_id: int) -> List[str]:
        """Получить теги статьи"""
        # TODO: реализовать получение тегов
        return []

    async def _get_favorites_count(self, article_id: int) -> int:
        """Получить количество избранных"""
        # TODO: реализовать подсчёт
        return 0

    async def _get_comments_count(self, article_id: int) -> int:
        """Получить количество комментариев"""
        # TODO: реализовать подсчёт
        return 0

    async def _is_favorited(self, article_id: int, user_id: Optional[int]) -> bool:
        """Проверить, добавлена ли статья в избранное"""
        if not user_id:
            return False
        # TODO: реализовать проверку
        return False

    async def create_article(self, article_dto: ArticleCreateDTO, author_id: int) -> ArticleResponseDTO:
        """Создание статьи"""
        # Проверка уникальности slug
        existing = await self.article_repo.get_by_slug(article_dto.slug)
        if existing:
            raise ValueError("Slug already exists")

        # Создание статьи в БД
        article_db = ArticleDB(
            title=article_dto.title,
            description=article_dto.description,
            body=article_dto.body,
            slug=article_dto.slug,
            author_id=author_id
        )

        created = await self.article_repo.create(article_db)

        # Обработка тегов
        if article_dto.tags:
            for tag_name in article_dto.tags:
                tag = await self.tag_repo.get_or_create(tag_name)
                # TODO: добавить связь статьи с тегом

        # Получение DTO для ответа
        author_dto = await self._get_author_dto(author_id)
        tags = await self._get_tags_for_article(created.id)

        return ArticleResponseDTO(
            id=created.id,
            slug=created.slug,
            title=created.title,
            description=created.description,
            body=created.body,
            author=author_dto,
            tags=tags,
            favorited=False,
            favorites_count=0,
            comments_count=0,
            created_at=created.created_at,
            updated_at=created.updated_at
        )

    async def get_article_by_slug(self, slug: str, current_user_id: Optional[int] = None) -> Optional[
        ArticleResponseDTO]:
        """Получение статьи по slug"""
        article_db = await self.article_repo.get_by_slug(slug)
        if not article_db:
            return None

        author_dto = await self._get_author_dto(article_db.author_id, current_user_id)
        tags = await self._get_tags_for_article(article_db.id)
        favorites_count = await self._get_favorites_count(article_db.id)
        comments_count = await self._get_comments_count(article_db.id)
        favorited = await self._is_favorited(article_db.id, current_user_id)

        return ArticleResponseDTO(
            id=article_db.id,
            slug=article_db.slug,
            title=article_db.title,
            description=article_db.description,
            body=article_db.body,
            author=author_dto,
            tags=tags,
            favorited=favorited,
            favorites_count=favorites_count,
            comments_count=comments_count,
            created_at=article_db.created_at,
            updated_at=article_db.updated_at
        )

    async def list_articles(
            self,
            skip: int = 0,
            limit: int = 20,
            tag: Optional[str] = None,
            author: Optional[str] = None,
            favorited: Optional[str] = None,
            current_user_id: Optional[int] = None
    ) -> Tuple[List[ArticleResponseDTO], int]:
        """Получение списка статей с фильтрацией"""
        articles_db, total = await self.article_repo.get_list(
            skip=skip,
            limit=limit,
            tag=tag,
            author=author,
            favorited=favorited
        )

        result = []
        for article_db in articles_db:
            author_dto = await self._get_author_dto(article_db.author_id, current_user_id)
            tags = await self._get_tags_for_article(article_db.id)
            favorites_count = await self._get_favorites_count(article_db.id)
            comments_count = await self._get_comments_count(article_db.id)
            favorited_flag = await self._is_favorited(article_db.id, current_user_id)

            result.append(ArticleResponseDTO(
                id=article_db.id,
                slug=article_db.slug,
                title=article_db.title,
                description=article_db.description,
                body=article_db.body,
                author=author_dto,
                tags=tags,
                favorited=favorited_flag,
                favorites_count=favorites_count,
                comments_count=comments_count,
                created_at=article_db.created_at,
                updated_at=article_db.updated_at
            ))

        return result, total

    async def update_article(
            self,
            slug: str,
            update_dto: ArticleUpdateDTO,
            current_user_id: int
    ) -> ArticleResponseDTO:
        """Обновление статьи"""
        article_db = await self.article_repo.get_by_slug(slug)
        if not article_db:
            raise ValueError("Article not found")

        # Проверка прав (только автор)
        if article_db.author_id != current_user_id:
            raise PermissionError("You don't have permission to edit this article")

        # Обновление полей
        if update_dto.title:
            article_db.title = update_dto.title
        if update_dto.description is not None:
            article_db.description = update_dto.description
        if update_dto.body:
            article_db.body = update_dto.body
        if update_dto.slug:
            # Проверка уникальности нового slug
            existing = await self.article_repo.get_by_slug(update_dto.slug)
            if existing and existing.id != article_db.id:
                raise ValueError("Slug already exists")
            article_db.slug = update_dto.slug

        article_db.updated_at = datetime.now()
        await self.article_repo.update(article_db)

        return await self.get_article_by_slug(article_db.slug, current_user_id)

    async def delete_article(self, slug: str, current_user_id: int) -> None:
        """Удаление статьи"""
        article_db = await self.article_repo.get_by_slug(slug)
        if not article_db:
            raise ValueError("Article not found")

        if article_db.author_id != current_user_id:
            raise PermissionError("You don't have permission to delete this article")

        await self.article_repo.delete(article_db)


async def get_article_service(
        article_repo: ArticleRepo,
        user_repo: UserRepo,
        tag_repo: TagRepo
) -> ArticleService:
    """Dependency для получения ArticleService"""
    return ArticleService(article_repo, user_repo, tag_repo)
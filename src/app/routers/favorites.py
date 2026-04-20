from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Article, User, Favorite, Tag, ArticleTag
from app.schemas.article import ArticleResponse
from app.schemas.wrappers import ArticleResponseWrapper

# ВАЖНО: prefix="/articles", а НЕ "/favorites"
router = APIRouter(prefix="/articles", tags=["Favorites"])


@router.post("/{slug}/favorite", response_model=ArticleResponseWrapper, summary="Добавить статью в избранное")
async def favorite_article(
        slug: str,
        user_id: int = Query(..., description="ID пользователя"),
        db: AsyncSession = Depends(get_db)
):
    """
    Добавить статью в избранное.

    - **slug**: уникальный идентификатор статьи
    """
    # Находим статью
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, f"Article with slug '{slug}' not found")

    # Проверяем пользователя
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, f"User with id {user_id} not found")

    # Проверяем, не в избранном ли уже
    existing = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.article_id == article.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Article already in favorites")

    # Добавляем в избранное
    favorite = Favorite(user_id=user_id, article_id=article.id)
    db.add(favorite)
    await db.commit()

    # Возвращаем обновлённую статью
    return await get_article_with_favorite_status(slug, user_id, db)


@router.delete("/{slug}/favorite", response_model=ArticleResponseWrapper, summary="Удалить статью из избранного")
async def unfavorite_article(
        slug: str,
        user_id: int = Query(..., description="ID пользователя"),
        db: AsyncSession = Depends(get_db)
):
    """
    Удалить статью из избранного.

    - **slug**: уникальный идентификатор статьи
    """
    # Находим статью
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, f"Article with slug '{slug}' not found")

    # Находим запись в избранном
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.article_id == article.id
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(404, "Favorite not found")

    # Удаляем
    await db.delete(favorite)
    await db.commit()

    # Возвращаем обновлённую статью
    return await get_article_with_favorite_status(slug, user_id, db)


async def get_article_with_favorite_status(slug: str, user_id: int, db: AsyncSession):
    """Вспомогательная функция для получения статьи со статусом избранного"""
    from app.models import Comment

    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(404, "Article not found")

    author = await db.get(User, article.author_id)

    # Получаем теги
    tags_result = await db.execute(
        select(Tag.tag)
        .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        .where(ArticleTag.article_id == article.id)
    )
    tags = [row[0] for row in tags_result.all()]

    # Количество избранных
    favorites_count_result = await db.execute(
        select(func.count()).select_from(Favorite).where(Favorite.article_id == article.id)
    )
    favorites_count = favorites_count_result.scalar() or 0

    # Количество комментариев
    comments_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.article_id == article.id)
    )
    comments_count = comments_count_result.scalar() or 0

    # Статус избранного для текущего пользователя
    favorited_result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.article_id == article.id
        )
    )
    favorited = favorited_result.scalar_one_or_none() is not None

    article_response = ArticleResponse(
        id=article.id,
        title=article.title,
        description=article.description,
        body=article.body,
        slug=article.slug,
        author=author,
        tags=tags,
        favorited=favorited,
        favorites_count=favorites_count,
        comments_count=comments_count,
        created_at=article.created_at,
        updated_at=article.updated_at
    )

    return ArticleResponseWrapper(article=article_response.model_dump())
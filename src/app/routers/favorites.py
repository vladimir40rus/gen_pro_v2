from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models import Favorite, Article
from app.schemas.article import ArticleResponse

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("/", summary="Добавить в избранное")
async def add_to_favorites(
        user_id: int,
        article_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Добавить статью в избранное"""
    # Проверяем, есть ли уже в избранном
    existing = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.article_id == article_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Article already in favorites")

    # Добавляем
    favorite = Favorite(user_id=user_id, article_id=article_id)
    db.add(favorite)
    await db.commit()
    return {"message": "Article added to favorites"}


@router.delete("/", summary="Удалить из избранного")
async def remove_from_favorites(
        user_id: int,
        article_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Удалить статью из избранного"""
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.article_id == article_id
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(404, "Favorite not found")

    await db.delete(favorite)
    await db.commit()
    return {"message": "Article removed from favorites"}


@router.get("/{user_id}", response_model=List[ArticleResponse], summary="Получить избранные статьи пользователя")
async def get_user_favorites(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить все избранные статьи пользователя"""
    from app.models import Article, User
    from app.schemas.article import ArticleResponse

    query = (
        select(Article)
        .join(Favorite, Article.id == Favorite.article_id)
        .where(Favorite.user_id == user_id)
    )
    result = await db.execute(query)
    articles = result.scalars().all()

    response = []
    for article in articles:
        author = await db.get(User, article.author_id)
        response.append(ArticleResponse(
            id=article.id,
            title=article.title,
            description=article.description,
            body=article.body,
            slug=article.slug,
            author=author,
            tags=[],
            favorited=True,
            favorites_count=0,
            comments_count=0,
            created_at=article.created_at,
            updated_at=article.updated_at
        ))
    return response
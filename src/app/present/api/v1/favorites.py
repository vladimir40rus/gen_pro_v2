from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra_external.connection_manager.db_connection import get_db_session
from app.infra_external.models.favorite_db import FavoriteDB
from app.infra_external.models.article_db import ArticleDB
from app.infra_external.models.user_db import UserDB

router = APIRouter(tags=["Favorites"])


async def get_current_user(db: AsyncSession) -> UserDB:
    result = await db.execute(select(UserDB).order_by(UserDB.id).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.post(
    "/articles/{slug}/favorite",
    status_code=status.HTTP_200_OK,
    summary="Добавить в избранное",
)
async def favorite_article(
    slug: str,
    db: AsyncSession = Depends(get_db_session)
):
    current_user = await get_current_user(db)
    article_result = await db.execute(select(ArticleDB).where(ArticleDB.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        return JSONResponse(status_code=404, content={"error": "Article not found"})

    existing = await db.execute(
        select(FavoriteDB).where(
            FavoriteDB.user_id == current_user.id,
            FavoriteDB.article_id == article.id
        )
    )
    if existing.scalar_one_or_none():
        return JSONResponse(status_code=400, content={"error": "Already in favorites"})

    favorite = FavoriteDB(user_id=current_user.id, article_id=article.id)
    db.add(favorite)
    await db.commit()

    return {"message": "Added to favorites"}


@router.delete(
    "/articles/{slug}/favorite",
    status_code=status.HTTP_200_OK,
    summary="Удалить из избранного",
)
async def unfavorite_article(
    slug: str,
    db: AsyncSession = Depends(get_db_session)
):
    current_user = await get_current_user(db)
    article_result = await db.execute(select(ArticleDB).where(ArticleDB.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        return JSONResponse(status_code=404, content={"error": "Article not found"})

    favorite = await db.execute(
        select(FavoriteDB).where(
            FavoriteDB.user_id == current_user.id,
            FavoriteDB.article_id == article.id
        )
    )
    favorite = favorite.scalar_one_or_none()
    if not favorite:
        return JSONResponse(status_code=404, content={"error": "Favorite not found"})

    await db.delete(favorite)
    await db.commit()

    return {"message": "Removed from favorites"}
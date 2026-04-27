from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models import Article, User, Favorite, Tag, ArticleTag, Comment
from app.schemas.wrappers import ArticleResponseWrapper

router = APIRouter(prefix="/articles", tags=["Favorites"])


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def get_author_stats(user_id: int, db: AsyncSession) -> dict:
    """Получить статистику автора"""
    from app.models import Follower

    followers_count_result = await db.execute(
        select(func.count()).select_from(Follower).where(Follower.following_id == user_id)
    )
    followers_count = followers_count_result.scalar() or 0

    following_count_result = await db.execute(
        select(func.count()).select_from(Follower).where(Follower.follower_id == user_id)
    )
    following_count = following_count_result.scalar() or 0

    articles_count_result = await db.execute(
        select(func.count()).select_from(Article).where(Article.author_id == user_id)
    )
    articles_count = articles_count_result.scalar() or 0

    return {
        "followers_count": followers_count,
        "following_count": following_count,
        "articles_count": articles_count
    }


async def get_article_by_slug(slug: str, db: AsyncSession, user_id: Optional[int] = None):
    """Получить статью по slug с дополнительной информацией"""
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        return None

    author = await db.get(User, article.author_id)

    tags_result = await db.execute(
        select(Tag.tag)
        .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        .where(ArticleTag.article_id == article.id)
    )
    tags = [row[0] for row in tags_result.all()]

    favorites_count_result = await db.execute(
        select(func.count()).select_from(Favorite).where(Favorite.article_id == article.id)
    )
    favorites_count = favorites_count_result.scalar() or 0

    comments_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.article_id == article.id)
    )
    comments_count = comments_count_result.scalar() or 0

    favorited = False
    if user_id:
        fav_result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.article_id == article.id
            )
        )
        favorited = fav_result.scalar_one_or_none() is not None

    return {
        "article": article,
        "author": author,
        "tags": tags,
        "favorited": favorited,
        "favorites_count": favorites_count,
        "comments_count": comments_count
    }


def format_article_response(article_data: dict, author_stats: dict = None) -> dict:
    """Форматирует статью для ответа"""
    article = article_data["article"]
    author = article_data["author"]

    if author_stats is None:
        author_stats = {
            "followers_count": 0,
            "following_count": 0,
            "articles_count": 0
        }

    return {
        "id": article.id,
        "slug": article.slug,
        "title": article.title,
        "description": article.description,
        "body": article.body,
        "author": {
            "username": author.username,
            "bio": author.bio,
            "image_url": author.image_url,
            "following": False,
            "followers_count": author_stats["followers_count"],
            "following_count": author_stats["following_count"],
            "articles_count": author_stats["articles_count"]
        },
        "tags": article_data["tags"],
        "favorited": article_data["favorited"],
        "favorites_count": article_data["favorites_count"],
        "comments_count": article_data["comments_count"],
        "created_at": article.created_at.isoformat() if article.created_at else None,
        "updated_at": article.updated_at.isoformat() if article.updated_at else None
    }


# ========== ЭНДПОИНТЫ ИЗБРАННОГО ==========

@router.post(
    "/{slug}/favorite",
    response_model=ArticleResponseWrapper,
    status_code=status.HTTP_200_OK,
    summary="Добавить в избранное",
    description="Добавляет статью в избранное пользователя",
    responses={
        200: {
            "description": "Статья добавлена в избранное",
            "content": {
                "application/json": {
                    "example": {
                        "article": {
                            "id": 456,
                            "slug": "how-to-learn-javascript-in-2024",
                            "title": "How to Learn JavaScript in 2024",
                            "description": "A comprehensive guide to learning JavaScript",
                            "body": "JavaScript is one of the most popular programming languages...",
                            "author": {
                                "username": "johndoe",
                                "bio": "Full-stack developer",
                                "image_url": "https://storage.com/avatars/123.jpg",
                                "following": True,
                                "followers_count": 42,
                                "following_count": 15,
                                "articles_count": 7
                            },
                            "tags": ["javascript"],
                            "favorited": True,
                            "favorites_count": 42,
                            "comments_count": 15,
                            "created_at": "2024-02-01T14:20:00Z",
                            "updated_at": "2024-02-05T09:15:00Z"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Не аутентифицирован"
        },
        404: {
            "description": "Статья не найдена",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Article not found"
                    }
                }
            }
        }
    }
)
async def favorite_article(
        slug: str,
        user_id: int = Query(..., description="ID пользователя (временно)"),
        db: AsyncSession = Depends(get_db)
):
    """Добавить статью в избранное"""

    # Проверяем существование пользователя
    user = await db.get(User, user_id)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    # Находим статью
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        return JSONResponse(
            status_code=404,
            content={"error": "Article not found"}
        )

    # Проверяем, не в избранном ли уже
    existing = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.article_id == article.id
        )
    )
    if existing.scalar_one_or_none():
        # Если уже в избранном, просто возвращаем статью
        article_info = await get_article_by_slug(slug, db, user_id)
        author_stats = await get_author_stats(article.author_id, db)
        return ArticleResponseWrapper(article=format_article_response(article_info, author_stats))

    # Добавляем в избранное
    favorite = Favorite(user_id=user_id, article_id=article.id)
    db.add(favorite)
    await db.commit()

    # Возвращаем обновлённую статью
    article_info = await get_article_by_slug(slug, db, user_id)
    author_stats = await get_author_stats(article.author_id, db)

    return ArticleResponseWrapper(article=format_article_response(article_info, author_stats))


@router.delete(
    "/{slug}/favorite",
    response_model=ArticleResponseWrapper,
    status_code=status.HTTP_200_OK,
    summary="Удалить из избранного",
    description="Удаляет статью из избранного пользователя",
    responses={
        200: {
            "description": "Статья удалена из избранного",
            "content": {
                "application/json": {
                    "example": {
                        "article": {
                            "id": 456,
                            "slug": "how-to-learn-javascript-in-2024",
                            "title": "How to Learn JavaScript in 2024",
                            "description": "A comprehensive guide to learning JavaScript",
                            "body": "JavaScript is one of the most popular programming languages...",
                            "author": {
                                "username": "johndoe",
                                "bio": "Full-stack developer",
                                "image_url": "https://storage.com/avatars/123.jpg",
                                "following": True,
                                "followers_count": 42,
                                "following_count": 15,
                                "articles_count": 7
                            },
                            "tags": ["javascript"],
                            "favorited": False,
                            "favorites_count": 41,
                            "comments_count": 15,
                            "created_at": "2024-02-01T14:20:00Z",
                            "updated_at": "2024-02-05T09:15:00Z"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Не аутентифицирован"
        },
        404: {
            "description": "Статья не найдена",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Article not found"
                    }
                }
            }
        }
    }
)
async def unfavorite_article(
        slug: str,
        user_id: int = Query(..., description="ID пользователя (временно)"),
        db: AsyncSession = Depends(get_db)
):
    """Удалить статью из избранного"""

    # Проверяем существование пользователя
    user = await db.get(User, user_id)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    # Находим статью
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        return JSONResponse(
            status_code=404,
            content={"error": "Article not found"}
        )

    # Находим запись в избранном
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.article_id == article.id
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        # Если нет в избранном, просто возвращаем статью
        article_info = await get_article_by_slug(slug, db, user_id)
        author_stats = await get_author_stats(article.author_id, db)
        return ArticleResponseWrapper(article=format_article_response(article_info, author_stats))

    # Удаляем из избранного
    await db.delete(favorite)
    await db.commit()

    # Возвращаем обновлённую статью
    article_info = await get_article_by_slug(slug, db, user_id)
    author_stats = await get_author_stats(article.author_id, db)

    return ArticleResponseWrapper(article=format_article_response(article_info, author_stats))
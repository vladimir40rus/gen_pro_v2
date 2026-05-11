from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models import Comment, Article, User, Tag, ArticleTag, Favorite
from app.schemas.comment import CommentCreate, CommentCreateWrapper, CommentUpdate, CommentUpdateWrapper, \
    CommentResponse
from app.schemas.wrappers import CommentResponseWrapper, CommentsResponseWrapper

router = APIRouter(prefix="/articles", tags=["Comments"])


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def get_author_stats(user_id: int, db: AsyncSession) -> dict:
    """Получить статистику автора"""
    from app.models import Follower, Article

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


async def get_comment_with_author(comment: Comment, db: AsyncSession, current_user_id: Optional[int] = None) -> dict:
    """Получить комментарий с информацией об авторе"""
    author = await db.get(User, comment.author_id)
    author_stats = await get_author_stats(author.id, db)

    # Проверяем, подписан ли текущий пользователь на автора
    following = False
    if current_user_id:
        from app.models import Follower
        follow_result = await db.execute(
            select(Follower).where(
                Follower.follower_id == current_user_id,
                Follower.following_id == author.id
            )
        )
        following = follow_result.scalar_one_or_none() is not None

    return {
        "id": comment.id,
        "body": comment.body,
        "author": {
            "username": author.username,
            "bio": author.bio,
            "image_url": author.image_url,
            "following": following,
            "followers_count": author_stats["followers_count"],
            "following_count": author_stats["following_count"],
            "articles_count": author_stats["articles_count"]
        },
        "article_id": comment.article_id,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
    }


# ========== ЭНДПОИНТЫ ==========

@router.post(
    "/{slug}/comments",
    response_model=CommentResponseWrapper,
    status_code=status.HTTP_201_CREATED,
    summary="Добавление комментария",
    description="Добавляет новый комментарий к статье",
    responses={
        201: {
            "description": "Комментарий добавлен",
            "content": {
                "application/json": {
                    "example": {
                        "comment": {
                            "id": 789,
                            "body": "Great article! Very helpful.",
                            "author": {
                                "username": "johndoe",
                                "bio": "Full-stack developer",
                                "image_url": "https://storage.com/avatars/123.jpg",
                                "following": True,
                                "followers_count": 42,
                                "following_count": 15,
                                "articles_count": 7
                            },
                            "article_id": 456,
                            "created_at": "2024-02-02T10:30:00Z",
                            "updated_at": "2024-02-02T11:15:00Z"
                        }
                    }
                }
            }
        },
        401: {"description": "Не аутентифицирован"},
        404: {"description": "Статья не найдена"},
        422: {"description": "Ошибка валидации"}
    }
)
async def create_comment(
        slug: str,
        comment_data: CommentCreateWrapper,
        user_id: int = Query(..., description="ID пользователя (временно)"),
        db: AsyncSession = Depends(get_db)
):
    """Добавить новый комментарий к статье"""

    # Находим статью
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        return JSONResponse(
            status_code=404,
            content={"error": "Article not found"}
        )

    # Проверяем пользователя
    user = await db.get(User, user_id)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    # Создаём комментарий
    comment = Comment(
        body=comment_data.comment.body,
        article_id=article.id,
        author_id=user_id
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    comment_response = await get_comment_with_author(comment, db, user_id)

    return CommentResponseWrapper(comment=comment_response)


@router.get(
    "/{slug}/comments",
    response_model=CommentsResponseWrapper,
    summary="Получение комментариев к статье",
    description="Возвращает все комментарии к указанной статье",
    responses={
        200: {
            "description": "Комментарии к статье",
            "content": {
                "application/json": {
                    "example": {
                        "comments": [
                            {
                                "id": 789,
                                "body": "Great article! Very helpful.",
                                "author": {
                                    "username": "johndoe",
                                    "bio": "Full-stack developer",
                                    "image_url": "https://storage.com/avatars/123.jpg",
                                    "following": True,
                                    "followers_count": 42,
                                    "following_count": 15,
                                    "articles_count": 7
                                },
                                "article_id": 456,
                                "created_at": "2024-02-02T10:30:00Z",
                                "updated_at": "2024-02-02T11:15:00Z"
                            }
                        ]
                    }
                }
            }
        },
        404: {"description": "Статья не найдена"}
    }
)
async def get_article_comments(
        slug: str = Path(..., description="Уникальный идентификатор статьи",
                         examples=["how-to-learn-javascript-in-2024"]),
        limit: int = Query(20, ge=1, le=100, description="Количество записей на странице", examples=[20]),
        offset: int = Query(0, ge=0, description="Смещение для пагинации", examples=[0]),
        db: AsyncSession = Depends(get_db)
):
    """Получить все комментарии к статье"""

    # Находим статью
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        return JSONResponse(
            status_code=404,
            content={"error": "Article not found"}
        )

    # Получаем комментарии
    result = await db.execute(
        select(Comment)
        .where(Comment.article_id == article.id)
        .order_by(desc(Comment.created_at))
        .offset(offset)
        .limit(limit)
    )
    comments = result.scalars().all()

    # Формируем ответ
    response_comments = []
    for comment in comments:
        comment_response = await get_comment_with_author(comment, db, None)
        response_comments.append(comment_response)

    return CommentsResponseWrapper(comments=response_comments)


@router.put(
    "/{slug}/comments/{comment_id}",
    response_model=CommentResponseWrapper,
    summary="Редактирование комментария",
    description="Обновляет существующий комментарий (только автор)",
    responses={
        200: {
            "description": "Комментарий обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "comment": {
                            "id": 789,
                            "body": "Great article! Very helpful.",
                            "author": {
                                "username": "johndoe",
                                "bio": "Full-stack developer",
                                "image_url": "https://storage.com/avatars/123.jpg",
                                "following": True,
                                "followers_count": 42,
                                "following_count": 15,
                                "articles_count": 7
                            },
                            "article_id": 456,
                            "created_at": "2024-02-02T10:30:00Z",
                            "updated_at": "2024-02-02T11:15:00Z"
                        }
                    }
                }
            }
        },
        401: {"description": "Не аутентифицирован"},
        403: {"description": "Нет прав (не автор)"},
        404: {"description": "Комментарий не найден"}
    }
)
async def update_comment(
        comment_data: CommentUpdateWrapper,
        user_id: int = Query(..., description="ID пользователя (для проверки прав)"),
        slug: str = Path(..., description="Уникальный идентификатор статьи",
                         examples=["how-to-learn-javascript-in-2024"]),
        comment_id: int = Path(..., description="ID комментария", examples=[789]),
        db: AsyncSession = Depends(get_db)
):
    """Обновить комментарий (только автор)"""

    # Находим комментарий
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        return JSONResponse(
            status_code=404,
            content={"error": "Comment not found"}
        )

    # Проверяем права
    if comment.author_id != user_id:
        return JSONResponse(
            status_code=403,
            content={"error": "You don't have permission to edit this comment"}
        )

    # Обновляем
    if comment_data.comment.body is not None:
        comment.body = comment_data.comment.body

    await db.commit()
    await db.refresh(comment)

    comment_response = await get_comment_with_author(comment, db, user_id)

    return CommentResponseWrapper(comment=comment_response)


@router.delete(
    "/{slug}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление комментария",
    description="Удаляет комментарий (только автор)",
    responses={
        204: {"description": "Комментарий удален"},
        401: {"description": "Не аутентифицирован"},
        403: {"description": "Нет прав (не автор)"},
        404: {"description": "Комментарий не найден"}
    }
)
async def delete_comment(
        user_id: int = Query(..., description="ID пользователя (для проверки прав)"),
        slug: str = Path(..., description="Уникальный идентификатор статьи",
                         examples=["how-to-learn-javascript-in-2024"]),
        comment_id: int = Path(..., description="ID комментария", examples=[789]),
        db: AsyncSession = Depends(get_db)
):
    """Удалить комментарий (только автор)"""

    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        return JSONResponse(
            status_code=404,
            content={"error": "Comment not found"}
        )

    if comment.author_id != user_id:
        return JSONResponse(
            status_code=403,
            content={"error": "You don't have permission to delete this comment"}
        )

    await db.delete(comment)
    await db.commit()

    return None
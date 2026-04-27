from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Annotated

from app.database import get_db
from app.models import Comment, Article, User
from app.schemas.comment import (
    CommentResponse,
    Author,
    CreateCommentRequest,
    UpdateCommentRequest,
    CommentResponseWrapper,
    CommentsResponseWrapper
)

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/articles/{slug}/comments", response_model=CommentResponseWrapper,
             status_code=status.HTTP_201_CREATED,
             summary="Добавление комментария к статье")
async def create_comment(
    comment_data: CreateCommentRequest,
    slug: str = Path(..., description="Уникальный идентификатор статьи", example="how-to-learn-javascript-in-2024"),
    # user_id: int = Query(..., description="ID пользователя (временное решение без JWT)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Добавить новый комментарий к статье.

    - **slug**: уникальный идентификатор статьи
    - **comment_data**: объект с полем comment, содержащим текст комментария
    - **user_id**: ID автора комментария (временно передается в query)
    """
    # Находим статью по slug
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, f"Article with slug '{slug}' not found")

    # Проверяем существование пользователя
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, f"User with id {user_id} not found")

    # Создаем комментарий
    comment = Comment(
        body=comment_data.comment.body,
        article_id=article.id,
        author_id=user_id
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    # Формируем ответ
    comment_response = CommentResponse(
        id=comment.id,
        body=comment.body,
        author=Author(
            username=user.username,
            bio=user.bio,
            image_url=user.image_url,
            following=True,  # заглушка
            followers_count=42,  # заглушка
            following_count=15,  # заглушка
            articles_count=7  # заглушка
        ),
        article_id=article.id,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )

    return CommentResponseWrapper(comment=comment_response)


@router.get("/articles/{slug}/comments", response_model=CommentsResponseWrapper,
            summary="Получение комментариев к статье")
async def get_article_comments(
        slug: Annotated[str, Path(description="Уникальный идентификатор статьи", examples=["how-to-learn-javascript-in-2024"])],
        skip: int = Query(0, ge=0, description="Количество комментариев для пропуска"),
        limit: int = Query(20, ge=1, le=100, description="Максимальное количество комментариев"),
        db: AsyncSession = Depends(get_db)
):
    """
    Получить все комментарии к статье с пагинацией.

    - **slug**: уникальный идентификатор статьи
    - **skip**: сколько комментариев пропустить
    - **limit**: максимальное количество комментариев
    """
    # Находим статью по slug
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, f"Article with slug '{slug}' not found")

    # Подсчет общего количества комментариев
    total_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.article_id == article.id)
    )
    total_count = total_count_result.scalar() or 0

    # Получаем комментарии с пагинацией
    result = await db.execute(
        select(Comment)
        .where(Comment.article_id == article.id)
        .order_by(desc(Comment.created_at))
        .offset(skip)
        .limit(limit)
    )
    comments = result.scalars().all()

    # Формируем ответы
    response_comments = []
    for comment in comments:
        author = await db.get(User, comment.author_id)

        comment_response = CommentResponse(
            id=comment.id,
            body=comment.body,
            author=Author(
                username=author.username,
                bio=author.bio,
                image_url=author.image_url,
                following=False,  # заглушка
                followers_count=0,  # заглушка
                following_count=0,  # заглушка
                articles_count=0  # заглушка
            ),
            article_id=article.id,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        )
        response_comments.append(comment_response)

    return CommentsResponseWrapper(comments=response_comments, comments_count=total_count)


@router.put("/articles/{slug}/comments/{comment_id}", response_model=CommentResponseWrapper,
            summary="Редактирование комментария")
async def update_comment(
        slug: Annotated[str, Path(description="Уникальный идентификатор статьи", examples=["how-to-learn-javascript-in-2024"])],
        comment_id: Annotated[int, Path(description="ID комментария", examples=[789])],
        comment_data: UpdateCommentRequest,
        user_id: int = Query(..., description="ID пользователя (для проверки прав)"),
        db: AsyncSession = Depends(get_db)
):
    """
    Обновить существующий комментарий (только автор может редактировать).

    - **slug**: уникальный идентификатор статьи
    - **comment_id**: ID комментария
    - **comment_data**: новый текст комментария
    - **user_id**: ID пользователя (должен совпадать с автором)
    """
    # Проверяем существование статьи
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, f"Article with slug '{slug}' not found")

    # Находим комментарий
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(404, f"Comment with id {comment_id} not found")

    # Проверяем, что комментарий принадлежит статье
    if comment.article_id != article.id:
        raise HTTPException(400, "Comment does not belong to this article")

    # Проверяем права (только автор может редактировать)
    if comment.author_id != user_id:
        raise HTTPException(403, "You don't have permission to edit this comment")

    # Обновляем комментарий
    if comment_data.comment.body is not None:
        comment.body = comment_data.comment.body

    await db.commit()
    await db.refresh(comment)

    # Получаем автора
    author = await db.get(User, comment.author_id)

    # Формируем ответ
    comment_response = CommentResponse(
        id=comment.id,
        body=comment.body,
        author=Author(
            username=author.username,
            bio=author.bio,
            image_url=author.image_url,
            following=True,  # заглушка
            followers_count=42,  # заглушка
            following_count=15,  # заглушка
            articles_count=7  # заглушка
        ),
        article_id=article.id,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )

    return CommentResponseWrapper(comment=comment_response)


@router.delete("/articles/{slug}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Удаление комментария")
async def delete_comment(
        slug: Annotated[str, Path(description="Уникальный идентификатор статьи", examples=["how-to-learn-javascript-in-2024"])],
        comment_id: Annotated[int, Path(description="ID комментария", examples=[789])],
        user_id: int = Query(..., description="ID пользователя (для проверки прав)"),
        db: AsyncSession = Depends(get_db)
):
    """
    Удалить комментарий (только автор может удалить).

    - **slug**: уникальный идентификатор статьи
    - **comment_id**: ID комментария
    - **user_id**: ID пользователя (должен совпадать с автором)
    """
    # Проверяем существование статьи
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, f"Article with slug '{slug}' not found")

    # Находим комментарий
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(404, f"Comment with id {comment_id} not found")

    # Проверяем, что комментарий принадлежит статье
    if comment.article_id != article.id:
        raise HTTPException(400, "Comment does not belong to this article")

    # Проверяем права (только автор может удалить)
    if comment.author_id != user_id:
        raise HTTPException(403, "You don't have permission to delete this comment")

    await db.delete(comment)
    await db.commit()
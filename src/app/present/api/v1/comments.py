from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.infra_external.connection_manager.db_connection import get_db_session
from app.infra_external.models.comment_db import CommentDB
from app.infra_external.models.article_db import ArticleDB
from app.infra_external.models.user_db import UserDB
from app.present.contracts.comment_contracts import (
    CommentCreateContract, CommentCreateWrapperContract,
    CommentResponseContract, CommentResponseWrapperContract,
    CommentsResponseWrapperContract,
)

router = APIRouter(tags=["Comments"])


async def get_current_user(db: AsyncSession) -> UserDB:
    result = await db.execute(select(UserDB).order_by(UserDB.id).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.post(
    "/articles/{slug}/comments",
    response_model=CommentResponseWrapperContract,
    status_code=status.HTTP_201_CREATED,
    summary="Добавление комментария",
)
async def create_comment(
    slug: str,
    comment_data: CommentCreateWrapperContract,
    db: AsyncSession = Depends(get_db_session)
):
    current_user = await get_current_user(db)
    article_result = await db.execute(select(ArticleDB).where(ArticleDB.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        return JSONResponse(status_code=404, content={"error": "Article not found"})

    comment = CommentDB(
        body=comment_data.comment.body,
        article_id=article.id,
        author_id=current_user.id
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentResponseWrapperContract(comment={
        "id": comment.id,
        "body": comment.body,
        "author": {
            "username": current_user.username,
            "bio": current_user.bio,
            "image_url": current_user.image_url,
            "following": False,
            "followers_count": 0,
            "following_count": 0,
            "articles_count": 0
        },
        "article_id": article.id,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
    })


@router.get(
    "/articles/{slug}/comments",
    response_model=CommentsResponseWrapperContract,
    summary="Получение комментариев к статье",
)
async def get_article_comments(
    slug: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    article_result = await db.execute(select(ArticleDB).where(ArticleDB.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        return JSONResponse(status_code=404, content={"error": "Article not found"})

    result = await db.execute(
        select(CommentDB)
        .where(CommentDB.article_id == article.id)
        .order_by(desc(CommentDB.created_at))
        .offset(offset)
        .limit(limit)
    )
    comments = result.scalars().all()

    response_comments = []
    for comment in comments:
        author = await db.get(UserDB, comment.author_id)
        response_comments.append({
            "id": comment.id,
            "body": comment.body,
            "author": {
                "username": author.username,
                "bio": author.bio,
                "image_url": author.image_url,
                "following": False,
                "followers_count": 0,
                "following_count": 0,
                "articles_count": 0
            },
            "article_id": article.id,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
            "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
        })

    return CommentsResponseWrapperContract(comments=response_comments)


@router.delete(
    "/articles/{slug}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление комментария",
)
async def delete_comment(
    slug: str,
    comment_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    current_user = await get_current_user(db)
    result = await db.execute(select(CommentDB).where(CommentDB.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment or comment.author_id != current_user.id:
        return JSONResponse(status_code=404, content={"error": "Comment not found"})

    await db.delete(comment)
    await db.commit()
    return None
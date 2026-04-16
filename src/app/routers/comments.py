from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models import Comment, Article, User
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse, Author

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/", response_model=CommentResponse, summary="Добавление комментариев к статье")
async def create_comment(comment_data: CommentCreate, db: AsyncSession = Depends(get_db)):
    # Берем первую статью и первого пользователя для простоты
    article_result = await db.execute(select(Article).limit(1))
    article = article_result.scalar_one_or_none()
    if not article:
        raise HTTPException(400, "No articles found. Create an article first.")

    user_result = await db.execute(select(User).limit(1))
    author = user_result.scalar_one_or_none()
    if not author:
        raise HTTPException(400, "No users found. Create a user first.")

    comment = Comment(
        body=comment_data.body,
        article_id=article.id,
        author_id=author.id
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentResponse(
        id=comment.id,
        body=comment.body,
        author=Author(username=author.username, bio=author.bio, image=author.image_url),
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )


@router.get("/article/{article_id}", response_model=List[CommentResponse], summary="Получение комментариев к статье")
async def get_article_comments(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Comment).where(Comment.article_id == article_id).order_by(desc(Comment.created_at))
    )
    comments = result.scalars().all()

    response = []
    for comment in comments:
        author_result = await db.execute(select(User).where(User.id == comment.author_id))
        author = author_result.scalar_one()

        response.append(CommentResponse(
            id=comment.id,
            body=comment.body,
            author=Author(username=author.username, bio=author.bio, image=author.image_url),
            created_at=comment.created_at,
            updated_at=comment.updated_at
        ))

    return response


@router.delete("/{comment_id}", summary="Удаление комментария")
async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(404, "Comment not found")

    await db.delete(comment)
    await db.commit()
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, or_, asc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models import Article, User
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.post("/", response_model=ArticleResponse, summary="Создание новой статьи")
async def create_article(article_data: ArticleCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем уникальность slug
    existing = await db.execute(select(Article).where(Article.slug == article_data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Slug already exists")

    # Берем первого пользователя как автора (для простоты)
    user_result = await db.execute(select(User).limit(1))
    author = user_result.scalar_one_or_none()
    if not author:
        raise HTTPException(400, "No users found. Create a user first.")

    article = Article(
        title=article_data.title,
        description=article_data.description or "",
        body=article_data.body,
        slug=article_data.slug,
        author_id=author.id
    )

    db.add(article)
    await db.commit()
    await db.refresh(article)

    return ArticleResponse(
        id=article.id,
        title=article.title,
        description=article.description,
        body=article.body,
        slug=article.slug,
        author=author,
        tags=[],
        favorited=False,
        favorites_count=0,
        comments_count=0,
        created_at=article.created_at,
        updated_at=article.updated_at
    )


@router.get("/", response_model=List[ArticleResponse], summary="Получение списка статей")
async def list_articles(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """
        Получить список статей с пагинацией.

        Параметры:
        - **skip**: Количество статей для пропуска (по умолчанию 0)
        - **limit**: Максимальное количество статей на странице (по умолчанию 20, максимум 100)
        """
    result = await db.execute(
        select(Article).order_by(desc(Article.created_at)).offset(skip).limit(limit)
    )
    articles = result.scalars().all()

    # Получаем авторов
    response = []
    for article in articles:
        author_result = await db.execute(select(User).where(User.id == article.author_id))
        author = author_result.scalar_one()

        response.append(ArticleResponse(
            id=article.id,
            title=article.title,
            description=article.description,
            body=article.body,
            slug=article.slug,
            author=author,
            tags=[],
            favorited=False,
            favorites_count=0,
            comments_count=0,
            created_at=article.created_at,
            updated_at=article.updated_at
        ))

    return response


# ПОЛУЧЕНИЕ статьи по slug
@router.get("/{slug}", response_model=ArticleResponse, summary="Получение статьи по slug")
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(404, "Article not found")

    author = await db.get(User, article.author_id)

    return ArticleResponse(
        id=article.id,
        title=article.title,
        description=article.description,
        body=article.body,
        slug=article.slug,
        author=author,
        tags=[],
        favorited=False,
        favorites_count=0,
        comments_count=0,
        created_at=article.created_at,
        updated_at=article.updated_at
    )


# ОБНОВЛЕНИЕ статьи по slug
@router.put("/{slug}", response_model=ArticleResponse, summary="Обновление статьи по slug")
async def update_article(
        slug: str,
        article_data: ArticleUpdate,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(404, "Article not found")

    # Обновляем только то, что пришло
    if article_data.title:
        article.title = article_data.title
    if article_data.description:
        article.description = article_data.description
    if article_data.body:
        article.body = article_data.body
    if article_data.slug:
        article.slug = article_data.slug

    await db.commit()
    await db.refresh(article)

    author = await db.get(User, article.author_id)

    return ArticleResponse(
        id=article.id,
        title=article.title,
        description=article.description,
        body=article.body,
        slug=article.slug,
        author=author,
        tags=[],
        favorited=False,
        favorites_count=0,
        comments_count=0,
        created_at=article.created_at,
        updated_at=article.updated_at
    )


# УДАЛЕНИЕ статьи по slug
@router.delete("/{slug}", summary="Удаление статьи по slug")
async def delete_article(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(404, "Article not found")

    await db.delete(article)
    await db.commit()





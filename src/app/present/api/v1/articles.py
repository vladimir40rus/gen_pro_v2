from app.infra_external.models.follower_db import FollowerDB
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.infra_external.connection_manager.db_connection import get_db_session
from app.infra_external.models.article_db import ArticleDB
from app.infra_external.models.user_db import UserDB
from app.infra_external.models.tag_db import TagDB, article_tag_association
from app.infra_external.models.favorite_db import FavoriteDB
from app.infra_external.models.comment_db import CommentDB
from app.present.api.v1.contracts import (
    ArticleCreateWrapperContract,
    ArticleResponseWrapperContract,
    ArticlesResponseWrapperContract,
)

router = APIRouter(tags=["Articles"])


async def get_current_user(db: AsyncSession) -> UserDB:
    result = await db.execute(select(UserDB).order_by(UserDB.id).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user


def format_article(article: ArticleDB, author: UserDB, tags: List[str], favorited: bool, favorites_count: int, comments_count: int) -> dict:
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
            "followers_count": 0,
            "following_count": 0,
            "articles_count": 0
        },
        "tags": tags,
        "favorited": favorited,
        "favorites_count": favorites_count,
        "comments_count": comments_count,
        "created_at": article.created_at.isoformat() if article.created_at else None,
        "updated_at": article.updated_at.isoformat() if article.updated_at else None
    }


# ========== Создание статьи ==========
@router.post(
    "/articles",
    response_model=ArticleResponseWrapperContract,
    status_code=status.HTTP_201_CREATED,
    summary="Создание новой статьи",
)
async def create_article(
    create_data: ArticleCreateWrapperContract,
    db: AsyncSession = Depends(get_db_session)
):
    article_data = create_data.article
    current_user = await get_current_user(db)

    existing = await db.execute(select(ArticleDB).where(ArticleDB.slug == article_data.slug))
    if existing.scalar_one_or_none():
        return JSONResponse(status_code=422, content={"errors": {"slug": ["already exists"]}})

    article = ArticleDB(
        title=article_data.title,
        description=article_data.description or "",
        body=article_data.body,
        slug=article_data.slug,
        author_id=current_user.id
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    if article_data.tags:
        for tag_name in article_data.tags:
            tag_result = await db.execute(select(TagDB).where(TagDB.name == tag_name))
            tag = tag_result.scalar_one_or_none()
            if not tag:
                tag = TagDB(name=tag_name)
                db.add(tag)
                await db.flush()
            await db.execute(article_tag_association.insert().values(article_id=article.id, tag_id=tag.id))
        await db.commit()

    return ArticleResponseWrapperContract(article=format_article(article, current_user, article_data.tags or [], False, 0, 0))


# ========== Список статей ==========
@router.get(
    "/articles",
    response_model=ArticlesResponseWrapperContract,
    summary="Получение списка статей",
)
async def list_articles(
    tag: Optional[str] = Query(None, description="Фильтр по тегу"),
    author: Optional[str] = Query(None, description="Фильтр по автору"),
    favorited: Optional[str] = Query(None, description="Фильтр по избранному"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    query = select(ArticleDB)

    if author:
        author_result = await db.execute(select(UserDB).where(UserDB.username == author))
        author_user = author_result.scalar_one_or_none()
        if author_user:
            query = query.where(ArticleDB.author_id == author_user.id)

    if tag:
        query = query.join(article_tag_association).join(TagDB).where(TagDB.name == tag)

    if favorited:
        user_result = await db.execute(select(UserDB).where(UserDB.username == favorited))
        user = user_result.scalar_one_or_none()
        if user:
            query = query.join(FavoriteDB).where(FavoriteDB.user_id == user.id)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0

    query = query.order_by(desc(ArticleDB.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    response_articles = []
    for article in articles:
        author_db = await db.get(UserDB, article.author_id)
        tags_result = await db.execute(select(TagDB.name).join(article_tag_association).where(article_tag_association.c.article_id == article.id))
        tags = [row[0] for row in tags_result.all()]
        favorites_count = await db.execute(select(func.count()).select_from(FavoriteDB).where(FavoriteDB.article_id == article.id))
        comments_count = await db.execute(select(func.count()).select_from(CommentDB).where(CommentDB.article_id == article.id))
        favorited_flag = await db.execute(select(FavoriteDB).where(FavoriteDB.article_id == article.id, FavoriteDB.user_id == 1))  # упрощённо
        response_articles.append(format_article(article, author_db, tags, favorited_flag.scalar_one_or_none() is not None, favorites_count.scalar() or 0, comments_count.scalar() or 0))

    return ArticlesResponseWrapperContract(articles=response_articles, articles_count=total)


# ========== Лента статей (Feed) ==========
@router.get(
    "/articles/feed",
    response_model=ArticlesResponseWrapperContract,
    summary="Получение ленты статей",
    description="Возвращает статьи от авторов, на которых подписан пользователь",
    tags=["Feed"],
)
async def get_feed(
        limit: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
        offset: int = Query(0, ge=0, description="Смещение для пагинации"),
        db: AsyncSession = Depends(get_db_session)
):
    current_user = await get_current_user(db)

    # Находим подписки
    following_result = await db.execute(
        select(FollowerDB.following_id).where(FollowerDB.follower_id == current_user.id)
    )
    following_ids = [row[0] for row in following_result.all()]

    if not following_ids:
        return ArticlesResponseWrapperContract(articles=[], articles_count=0)

    # Подсчёт общего количества
    count_query = select(func.count()).select_from(ArticleDB).where(ArticleDB.author_id.in_(following_ids))
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar() or 0

    # Получаем статьи
    query = select(ArticleDB).where(ArticleDB.author_id.in_(following_ids))
    query = query.order_by(desc(ArticleDB.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    articles = result.scalars().all()

    # Формируем ответ
    response_articles = []
    for article in articles:
        author = await db.get(UserDB, article.author_id)
        tags_result = await db.execute(
            select(TagDB.name).join(article_tag_association).where(article_tag_association.c.article_id == article.id))
        tags = [row[0] for row in tags_result.all()]
        favorites_count = await db.execute(
            select(func.count()).select_from(FavoriteDB).where(FavoriteDB.article_id == article.id))
        comments_count = await db.execute(
            select(func.count()).select_from(CommentDB).where(CommentDB.article_id == article.id))

        response_articles.append(
            format_article(article, author, tags, False, favorites_count.scalar() or 0, comments_count.scalar() or 0))

    return ArticlesResponseWrapperContract(articles=response_articles, articles_count=total_count)


# ========== Поиск статей ==========
@router.get(
    "/search",
    response_model=ArticlesResponseWrapperContract,
    summary="Поиск статей",
    description="Полнотекстовый поиск по статьям",
)
async def search_articles(
        q: str = Query(..., min_length=3, description="Поисковый запрос (минимум 3 символа)"),
        tag: Optional[str] = Query(None, description="Фильтр по тегу"),
        author: Optional[str] = Query(None, description="Фильтр по автору"),
        limit: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
        offset: int = Query(0, ge=0, description="Смещение для пагинации"),
        sort: str = Query("relevance", pattern="^(relevance|newest|oldest)$", description="Сортировка результатов"),
        db: AsyncSession = Depends(get_db_session)
):
    query = select(ArticleDB)

    # Полнотекстовый поиск
    search_pattern = f"%{q}%"
    query = query.where(
        (ArticleDB.title.ilike(search_pattern)) |
        (ArticleDB.description.ilike(search_pattern)) |
        (ArticleDB.body.ilike(search_pattern))
    )

    # Фильтр по тегу
    if tag:
        query = query.join(article_tag_association).join(TagDB).where(TagDB.name == tag)

    # Фильтр по автору
    if author:
        author_result = await db.execute(select(UserDB).where(UserDB.username == author))
        author_user = author_result.scalar_one_or_none()
        if author_user:
            query = query.where(ArticleDB.author_id == author_user.id)
        else:
            return ArticlesResponseWrapperContract(articles=[], articles_count=0)

    # Сортировка
    if sort == "newest":
        query = query.order_by(desc(ArticleDB.created_at))
    elif sort == "oldest":
        query = query.order_by(asc(ArticleDB.created_at))
    else:  # relevance
        relevance_expr = func.length(ArticleDB.title) - func.length(func.replace(ArticleDB.title, q, ''))
        query = query.order_by(desc(relevance_expr), desc(ArticleDB.created_at))

    # Подсчёт общего количества
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0

    # Пагинация
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    # Формируем ответ
    response_articles = []
    for article in articles:
        author_db = await db.get(UserDB, article.author_id)
        tags_result = await db.execute(
            select(TagDB.name).join(article_tag_association).where(article_tag_association.c.article_id == article.id))
        tags = [row[0] for row in tags_result.all()]
        favorites_count = await db.execute(
            select(func.count()).select_from(FavoriteDB).where(FavoriteDB.article_id == article.id))
        comments_count = await db.execute(
            select(func.count()).select_from(CommentDB).where(CommentDB.article_id == article.id))

        response_articles.append(format_article(article, author_db, tags, False, favorites_count.scalar() or 0,
                                                comments_count.scalar() or 0))

    return ArticlesResponseWrapperContract(articles=response_articles, articles_count=total)
from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models import Article, User, Tag, ArticleTag, Favorite, Comment
from app.schemas.article import ArticleCreateWrapper, ArticleUpdateWrapper, ArticleUpdate
from app.schemas.wrappers import ArticleResponseWrapper, ArticlesResponseWrapper

router = APIRouter(prefix="/articles", tags=["Articles"])


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


# ========== ЭНДПОИНТЫ ==========

@router.post(
    "",
    response_model=ArticleResponseWrapper,
    status_code=status.HTTP_201_CREATED,
    summary="Создание новой статьи"
)
async def create_article(
        create_data: ArticleCreateWrapper,
        user_id: int = Query(..., description="ID автора (временно)"),
        db: AsyncSession = Depends(get_db)
):
    """Создать новую статью"""
    article_data = create_data.article
    errors = {}

    author = await db.get(User, user_id)
    if not author:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    existing = await db.execute(select(Article).where(Article.slug == article_data.slug))
    if existing.scalar_one_or_none():
        errors["slug"] = ["already exists"]

    if not article_data.title or len(article_data.title) < 3:
        errors["title"] = ["must be at least 3 characters"]

    if errors:
        return JSONResponse(
            status_code=422,
            content={"errors": errors}
        )

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

    if article_data.tags:
        for tag_name in article_data.tags:
            tag_result = await db.execute(select(Tag).where(Tag.tag == tag_name))
            tag = tag_result.scalar_one_or_none()
            if not tag:
                tag = Tag(tag=tag_name)
                db.add(tag)
                await db.flush()

            article_tag = ArticleTag(article_id=article.id, tag_id=tag.id)
            db.add(article_tag)
        await db.commit()

    author_stats = await get_author_stats(author.id, db)
    article_info = await get_article_by_slug(article.slug, db, user_id)

    return ArticleResponseWrapper(article=format_article_response(article_info, author_stats))


@router.get(
    "",
    response_model=ArticlesResponseWrapper,
    summary="Получение списка статей",
    description="Возвращает список статей с возможностью фильтрации"
)
async def list_articles(
        tag: Optional[str] = Query(None, description="Фильтр по тегу", examples=["javascript"]),
        author: Optional[str] = Query(None, description="Фильтр по автору (username)", examples=["johndoe"]),
        favorited: Optional[str] = Query(None, description="Фильтр по избранному пользователя (username)",
                                         examples=["johndoe"]),
        limit: int = Query(20, ge=1, le=100, description="Количество записей на странице", examples=[20]),
        offset: int = Query(0, ge=0, description="Смещение для пагинации", examples=[0]),
        user_id: Optional[int] = Query(None, description="ID текущего пользователя"),
        db: AsyncSession = Depends(get_db)
):
    """Получить список статей с фильтрацией и пагинацией"""

    query = select(Article)

    if author:
        author_result = await db.execute(select(User).where(User.username == author))
        author_user = author_result.scalar_one_or_none()
        if author_user:
            query = query.where(Article.author_id == author_user.id)
        else:
            return ArticlesResponseWrapper(articles=[], articles_count=0)

    if tag:
        query = query.join(ArticleTag).join(Tag).where(Tag.tag == tag)

    if favorited:
        user_result = await db.execute(select(User).where(User.username == favorited))
        user = user_result.scalar_one_or_none()
        if user:
            query = query.join(Favorite).where(Favorite.user_id == user.id)
        else:
            return ArticlesResponseWrapper(articles=[], articles_count=0)

    count_query = select(func.count()).select_from(query.subquery())
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar() or 0

    query = query.order_by(desc(Article.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    response_articles = []
    for article in articles:
        article_info = await get_article_by_slug(article.slug, db, user_id)
        author_stats = await get_author_stats(article.author_id, db)
        response_articles.append(format_article_response(article_info, author_stats))

    return ArticlesResponseWrapper(
        articles=response_articles,
        articles_count=total_count
    )


@router.get(
    "/{slug}",
    response_model=ArticleResponseWrapper,
    summary="Получение статьи по slug"
)
async def get_article(
        slug: str,
        user_id: Optional[int] = Query(None, description="ID текущего пользователя"),
        db: AsyncSession = Depends(get_db)
):
    """Получить статью по slug"""
    article_info = await get_article_by_slug(slug, db, user_id)

    if not article_info:
        return JSONResponse(
            status_code=404,
            content={"error": "Article not found"}
        )

    author_stats = await get_author_stats(article_info["article"].author_id, db)

    return ArticleResponseWrapper(article=format_article_response(article_info, author_stats))


@router.put(
    "/{slug}",
    response_model=ArticleResponseWrapper,
    summary="Обновление статьи",
    description="Обновляет существующую статью (только автор)"
)
async def update_article(
        slug: str,
        update_data: ArticleUpdateWrapper,
        user_id: int = Query(..., description="ID пользователя (для проверки прав)"),
        db: AsyncSession = Depends(get_db)
):
    """Обновить статью (только автор)"""

    article_info = await get_article_by_slug(slug, db, user_id)
    if not article_info:
        return JSONResponse(
            status_code=404,
            content={"error": "Article not found"}
        )

    article = article_info["article"]

    if article.author_id != user_id:
        return JSONResponse(
            status_code=403,
            content={"error": "You don't have permission to edit this article"}
        )

    article_data = update_data.article
    errors = {}

    if article_data.title is not None:
        if len(article_data.title) < 3:
            errors["title"] = ["must be at least 3 characters"]
        else:
            article.title = article_data.title

    if article_data.description is not None:
        article.description = article_data.description

    if article_data.body is not None:
        article.body = article_data.body

    if article_data.slug is not None:
        if article_data.slug != slug:
            existing = await db.execute(select(Article).where(Article.slug == article_data.slug))
            if existing.scalar_one_or_none():
                errors["slug"] = ["already exists"]
            else:
                article.slug = article_data.slug

    if errors:
        return JSONResponse(
            status_code=422,
            content={"errors": errors}
        )

    await db.commit()
    await db.refresh(article)

    updated_info = await get_article_by_slug(article.slug, db, user_id)
    author_stats = await get_author_stats(article.author_id, db)

    return ArticleResponseWrapper(article=format_article_response(updated_info, author_stats))


@router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление статьи",
    description="Удаляет статью и все связанные данные (комментарии, теги, лайки)"
)
async def delete_article(
        slug: str,
        user_id: int = Query(..., description="ID пользователя (для проверки прав) - временно"),
        db: AsyncSession = Depends(get_db)
):
    """Удалить статью (только автор)"""

    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        return JSONResponse(
            status_code=404,
            content={"error": "Article not found"}
        )

    if article.author_id != user_id:
        return JSONResponse(
            status_code=403,
            content={"error": "You don't have permission to delete this article"}
        )

    await db.delete(article)
    await db.commit()

    return None


# ========== ЛЕНТА СТАТЕЙ (FEED) ==========

@router.get(
    "/feed",
    response_model=ArticlesResponseWrapper,
    summary="Лента статей"
)
async def get_feed(
        user_id: int = Query(..., description="ID пользователя"),
        limit: int = Query(20, ge=1, le=100, description="Количество записей на странице", examples=[20]),
        offset: int = Query(0, ge=0, description="Смещение для пагинации", examples=[0]),
        db: AsyncSession = Depends(get_db)
):
    """Получить статьи авторов, на которых подписан пользователь"""

    user = await db.get(User, user_id)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    from app.models import Follower
    following_result = await db.execute(
        select(Follower.following_id).where(Follower.follower_id == user_id)
    )
    following_ids = [row[0] for row in following_result.all()]

    if not following_ids:
        return ArticlesResponseWrapper(articles=[], articles_count=0)

    count_query = select(func.count()).select_from(Article).where(Article.author_id.in_(following_ids))
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar() or 0

    query = select(Article).where(Article.author_id.in_(following_ids))
    query = query.order_by(desc(Article.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    articles = result.scalars().all()

    response_articles = []
    for article in articles:
        article_info = await get_article_by_slug(article.slug, db, user_id)
        author_stats = await get_author_stats(article.author_id, db)
        response_articles.append(format_article_response(article_info, author_stats))

    return ArticlesResponseWrapper(
        articles=response_articles,
        articles_count=total_count
    )


# ========== ПОИСК СТАТЕЙ ==========

@router.get(
    "/search",
    response_model=ArticlesResponseWrapper,
    summary="Поиск статей",
    description="Полнотекстовый поиск по статьям"
)
async def search_articles(
        q: str = Query(..., min_length=3, description="Поисковый запрос (минимум 3 символа)",
                       examples=["javascript tutorial"]),
        tag: Optional[str] = Query(None, description="Фильтр по тегу"),
        author: Optional[str] = Query(None, description="Фильтр по автору"),
        limit: int = Query(20, ge=1, le=100, description="Количество записей на странице", examples=[20]),
        offset: int = Query(0, ge=0, description="Смещение для пагинации", examples=[0]),
        sort: str = Query("relevance", pattern="^(relevance|newest|oldest)$", description="Сортировка результатов",
                          examples=["relevance"]),
        user_id: Optional[int] = Query(None, description="ID текущего пользователя (для проверки избранного)"),
        db: AsyncSession = Depends(get_db)
):
    """
    Полнотекстовый поиск по статьям.

    - **q**: поисковый запрос (обязательный, минимум 3 символа)
    - **tag**: фильтр по тегу
    - **author**: фильтр по автору
    - **limit**: количество записей на странице
    - **offset**: смещение для пагинации
    - **sort**: сортировка (relevance, newest, oldest)
    """

    query = select(Article)

    search_pattern = f"%{q}%"
    query = query.where(
        (Article.title.ilike(search_pattern)) |
        (Article.description.ilike(search_pattern)) |
        (Article.body.ilike(search_pattern))
    )

    if tag:
        query = query.join(ArticleTag).join(Tag).where(Tag.tag == tag)

    if author:
        author_result = await db.execute(select(User).where(User.username == author))
        author_user = author_result.scalar_one_or_none()
        if author_user:
            query = query.where(Article.author_id == author_user.id)
        else:
            return ArticlesResponseWrapper(articles=[], articles_count=0)

    if sort == "newest":
        query = query.order_by(desc(Article.created_at))
    elif sort == "oldest":
        query = query.order_by(asc(Article.created_at))
    else:
        relevance_expr = func.length(Article.title) - func.length(func.replace(Article.title, q, ''))
        query = query.order_by(desc(relevance_expr), desc(Article.created_at))

    count_query = select(func.count()).select_from(query.subquery())
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar() or 0

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    response_articles = []
    for article in articles:
        article_info = await get_article_by_slug(article.slug, db, user_id)
        author_stats = await get_author_stats(article.author_id, db)
        response_articles.append(format_article_response(article_info, author_stats))

    return ArticlesResponseWrapper(
        articles=response_articles,
        articles_count=total_count
    )
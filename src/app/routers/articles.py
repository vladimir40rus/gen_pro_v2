from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, or_, asc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models import Article, User, Tag, ArticleTag, Favorite
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse
from app.schemas.wrappers import ArticleResponseWrapper, ArticlesResponseWrapper

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.post("/", response_model=ArticleResponseWrapper, summary="Создание новой статьи")
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

    # Обработка тегов, если они переданы
    if article_data.tags:
        for tag_name in article_data.tags:
            # Найти или создать тег
            tag_result = await db.execute(select(Tag).where(Tag.tag == tag_name))
            tag = tag_result.scalar_one_or_none()
            if not tag:
                tag = Tag(tag=tag_name)
                db.add(tag)
                await db.flush()

            # Связать тег со статьей
            article_tag = ArticleTag(article_id=article.id, tag_id=tag.id)
            db.add(article_tag)

        await db.commit()

    # Формируем ответ
    article_response = ArticleResponse(
        id=article.id,
        title=article.title,
        description=article.description,
        body=article.body,
        slug=article.slug,
        author=author,
        tags=article_data.tags or [],
        favorited=False,
        favorites_count=0,
        comments_count=0,
        created_at=article.created_at,
        updated_at=article.updated_at
    )

    return ArticleResponseWrapper(article=article_response.model_dump())


@router.get("/", response_model=ArticlesResponseWrapper, summary="Получение списка статей")
async def list_articles(
        skip: int = Query(0, ge=0, description="Количество статей для пропуска"),
        limit: int = Query(20, ge=1, le=100, description="Максимальное количество статей на странице"),
        tag: Optional[str] = Query(None, description="Фильтр по тегу"),
        author: Optional[str] = Query(None, description="Фильтр по автору (username)"),
        favorited: Optional[str] = Query(None, description="Фильтр по избранному пользователя (username)"),
        db: AsyncSession = Depends(get_db)
):
    """
    Получить список статей с пагинацией и фильтрацией.

    Параметры:
    - **skip**: Количество статей для пропуска (по умолчанию 0)
    - **limit**: Максимальное количество статей на странице (по умолчанию 20, максимум 100)
    - **tag**: Фильтр по тегу (например: "python")
    - **author**: Фильтр по имени автора (например: "john_doe")
    - **favorited**: Фильтр по имени пользователя, который добавил в избранное
    """

    # Базовый запрос
    query = select(Article)

    # Фильтр по автору
    if author:
        author_result = await db.execute(select(User).where(User.username == author))
        author_user = author_result.scalar_one_or_none()
        if author_user:
            query = query.where(Article.author_id == author_user.id)
        else:
            # Автор не найден, возвращаем пустой результат
            return ArticlesResponseWrapper(articles=[], articles_count=0)

    # Фильтр по тегу
    if tag:
        query = query.join(ArticleTag).join(Tag).where(Tag.tag == tag)

    # Фильтр по избранному
    if favorited:
        user_result = await db.execute(select(User).where(User.username == favorited))
        user = user_result.scalar_one_or_none()
        if user:
            query = query.join(Favorite).where(Favorite.user_id == user.id)
        else:
            # Пользователь не найден, возвращаем пустой результат
            return ArticlesResponseWrapper(articles=[], articles_count=0)

    # Подсчет общего количества (для пагинации)
    count_query = select(func.count()).select_from(query.subquery())
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar() or 0

    # Пагинация и сортировка
    query = query.order_by(desc(Article.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    # Формируем ответы с дополнительной информацией
    response_articles = []
    for article in articles:
        # Получаем автора
        author_result = await db.execute(select(User).where(User.id == article.author_id))
        author = author_result.scalar_one()

        # Получаем теги статьи
        tags_result = await db.execute(
            select(Tag.tag)
            .join(ArticleTag, Tag.id == ArticleTag.tag_id)
            .where(ArticleTag.article_id == article.id)
        )
        tags = [row[0] for row in tags_result.all()]

        # Получаем количество избранных (лайков)
        favorites_count_result = await db.execute(
            select(func.count()).select_from(Favorite).where(Favorite.article_id == article.id)
        )
        favorites_count = favorites_count_result.scalar() or 0

        # Получаем количество комментариев
        from app.models import Comment
        comments_count_result = await db.execute(
            select(func.count()).select_from(Comment).where(Comment.article_id == article.id)
        )
        comments_count = comments_count_result.scalar() or 0

        article_response = ArticleResponse(
            id=article.id,
            title=article.title,
            description=article.description,
            body=article.body,
            slug=article.slug,
            author=author,
            tags=tags,
            favorited=False,  # TODO: проверять для текущего пользователя после добавления JWT
            favorites_count=favorites_count,
            comments_count=comments_count,
            created_at=article.created_at,
            updated_at=article.updated_at
        )
        response_articles.append(article_response.model_dump())

    return ArticlesResponseWrapper(
        articles=response_articles,
        articles_count=total_count
    )


@router.get("/{slug}", response_model=ArticleResponseWrapper, summary="Получение статьи по slug")
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(404, "Article not found")

    # Получаем автора
    author = await db.get(User, article.author_id)

    # Получаем теги статьи
    tags_result = await db.execute(
        select(Tag.tag)
        .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        .where(ArticleTag.article_id == article.id)
    )
    tags = [row[0] for row in tags_result.all()]

    # Получаем количество избранных
    favorites_count_result = await db.execute(
        select(func.count()).select_from(Favorite).where(Favorite.article_id == article.id)
    )
    favorites_count = favorites_count_result.scalar() or 0

    # Получаем количество комментариев
    from app.models import Comment
    comments_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.article_id == article.id)
    )
    comments_count = comments_count_result.scalar() or 0

    article_response = ArticleResponse(
        id=article.id,
        title=article.title,
        description=article.description,
        body=article.body,
        slug=article.slug,
        author=author,
        tags=tags,
        favorited=False,  # TODO: проверять для текущего пользователя
        favorites_count=favorites_count,
        comments_count=comments_count,
        created_at=article.created_at,
        updated_at=article.updated_at
    )

    return ArticleResponseWrapper(article=article_response.model_dump())


@router.put("/{slug}", response_model=ArticleResponseWrapper, summary="Обновление статьи по slug")
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
    if article_data.title is not None:
        article.title = article_data.title
    if article_data.description is not None:
        article.description = article_data.description
    if article_data.body is not None:
        article.body = article_data.body
    if article_data.slug is not None:
        # Проверяем уникальность нового slug
        if article_data.slug != slug:
            existing = await db.execute(select(Article).where(Article.slug == article_data.slug))
            if existing.scalar_one_or_none():
                raise HTTPException(400, "Slug already exists")
        article.slug = article_data.slug

    await db.commit()
    await db.refresh(article)

    # Получаем автора
    author = await db.get(User, article.author_id)

    # Получаем теги статьи
    tags_result = await db.execute(
        select(Tag.tag)
        .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        .where(ArticleTag.article_id == article.id)
    )
    tags = [row[0] for row in tags_result.all()]

    # Получаем количество избранных
    favorites_count_result = await db.execute(
        select(func.count()).select_from(Favorite).where(Favorite.article_id == article.id)
    )
    favorites_count = favorites_count_result.scalar() or 0

    # Получаем количество комментариев
    from app.models import Comment
    comments_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.article_id == article.id)
    )
    comments_count = comments_count_result.scalar() or 0

    article_response = ArticleResponse(
        id=article.id,
        title=article.title,
        description=article.description,
        body=article.body,
        slug=article.slug,
        author=author,
        tags=tags,
        favorited=False,
        favorites_count=favorites_count,
        comments_count=comments_count,
        created_at=article.created_at,
        updated_at=article.updated_at
    )

    return ArticleResponseWrapper(article=article_response.model_dump())


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT, summary="Удаление статьи по slug")
async def delete_article(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(404, "Article not found")

    await db.delete(article)
    await db.commit()


# ДОПОЛНИТЕЛЬНЫЙ ЭНДПОИНТ: Лента статей (Feed)
@router.get("/feed/me", response_model=ArticlesResponseWrapper, summary="Лента статей")
async def get_feed(
        user_id: int = Query(..., description="ID пользователя для получения ленты"),
        skip: int = Query(0, ge=0, description="Количество статей для пропуска"),
        limit: int = Query(20, ge=1, le=100, description="Максимальное количество статей"),
        db: AsyncSession = Depends(get_db)
):
    """
    Получить статьи авторов, на которых подписан пользователь.
    Требуется user_id в query параметрах (упрощенная версия без JWT).
    """

    # Проверяем, существует ли пользователь
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    # Найти всех, на кого подписан пользователь
    following_result = await db.execute(
        select(Follower.following_id).where(Follower.follower_id == user_id)
    )
    following_ids = [row[0] for row in following_result.all()]

    if not following_ids:
        return ArticlesResponseWrapper(articles=[], articles_count=0)

    # Запрос для подсчета общего количества
    count_query = select(func.count()).select_from(Article).where(Article.author_id.in_(following_ids))
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar() or 0

    # Получить статьи этих авторов
    query = select(Article).where(Article.author_id.in_(following_ids))
    query = query.order_by(desc(Article.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    articles = result.scalars().all()

    # Формируем ответы
    response_articles = []
    for article in articles:
        author = await db.get(User, article.author_id)

        # Получаем теги
        tags_result = await db.execute(
            select(Tag.tag)
            .join(ArticleTag, Tag.id == ArticleTag.tag_id)
            .where(ArticleTag.article_id == article.id)
        )
        tags = [row[0] for row in tags_result.all()]

        article_response = ArticleResponse(
            id=article.id,
            title=article.title,
            description=article.description,
            body=article.body,
            slug=article.slug,
            author=author,
            tags=tags,
            favorited=False,
            favorites_count=0,  # Можно подсчитать при необходимости
            comments_count=0,  # Можно подсчитать при необходимости
            created_at=article.created_at,
            updated_at=article.updated_at
        )
        response_articles.append(article_response.model_dump())

    return ArticlesResponseWrapper(
        articles=response_articles,
        articles_count=total_count
    )
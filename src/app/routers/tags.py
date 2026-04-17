from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models import Tag, ArticleTag
from app.schemas.tag import TagResponse
from app.schemas.wrappers import TagsResponseWrapper

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", response_model=TagsResponseWrapper, summary="Получение всех тегов")
async def get_all_tags(db: AsyncSession = Depends(get_db)):
    """
    Получить список всех тегов в системе.

    Возвращает массив строк с названиями тегов.
    """
    result = await db.execute(select(Tag.tag).order_by(Tag.tag))
    tags = result.scalars().all()

    # OpenAPI спецификация ожидает просто список строк
    return TagsResponseWrapper(tags=tags)


@router.get("/popular", response_model=TagsResponseWrapper, summary="Получение популярных тегов")
async def get_popular_tags(
        limit: int = Query(10, ge=1, le=50, description="Количество популярных тегов"),
        min_articles: int = Query(1, ge=1, description="Минимальное количество статей с тегом"),
        db: AsyncSession = Depends(get_db)
):
    """
    Получить список популярных тегов, отсортированных по частоте использования.

    - **limit**: максимальное количество тегов (по умолчанию 10)
    - **min_articles**: минимальное количество статей с тегом (по умолчанию 1)

    Возвращает массив строк с названиями популярных тегов.
    """
    # Подсчитываем количество статей для каждого тега
    query = (
        select(Tag.tag, func.count(ArticleTag.article_id).label('articles_count'))
        .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        .group_by(Tag.id, Tag.tag)
        .having(func.count(ArticleTag.article_id) >= min_articles)
        .order_by(func.count(ArticleTag.article_id).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    popular_tags = [row[0] for row in result.all()]

    return TagsResponseWrapper(tags=popular_tags)


@router.get("/with-count", response_model=List[dict], summary="Получение тегов с количеством статей")
async def get_tags_with_count(
        sort_by: str = Query("count", pattern="^(count|name)$", description="Сортировка: count или name"),
        limit: Optional[int] = Query(None, ge=1, le=100, description="Лимит тегов"),
        db: AsyncSession = Depends(get_db)
):
    """
    Получить список тегов с количеством статей для каждого.

    - **sort_by**: сортировка по количеству статей (count) или по имени (name)
    - **limit**: ограничить количество тегов

    Возвращает массив объектов с полями: name (название тега) и count (количество статей).
    """
    # Подсчитываем количество статей для каждого тега
    query = (
        select(Tag.tag, func.count(ArticleTag.article_id).label('articles_count'))
        .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        .group_by(Tag.id, Tag.tag)
    )

    # Сортировка
    if sort_by == "count":
        query = query.order_by(func.count(ArticleTag.article_id).desc())
    else:  # sort_by == "name"
        query = query.order_by(Tag.tag)

    # Лимит
    if limit:
        query = query.limit(limit)

    result = await db.execute(query)
    tags_with_count = [
        {"name": row[0], "count": row[1]}
        for row in result.all()
    ]

    return tags_with_count


@router.get("/search/", response_model=TagsResponseWrapper, summary="Поиск тегов")
async def search_tags(
        q: str = Query(..., min_length=1, description="Поисковый запрос"),
        limit: int = Query(10, ge=1, le=50, description="Максимальное количество результатов"),
        db: AsyncSession = Depends(get_db)
):
    """
    Поиск тегов по частичному совпадению.

    - **q**: поисковый запрос (например: "java" найдет "javascript", "java", "java8")
    - **limit**: максимальное количество результатов

    Возвращает массив строк с названиями тегов, содержащих поисковый запрос.
    """
    # Поиск тегов, содержащих подстроку (регистронезависимый)
    query = (
        select(Tag.tag)
        .where(Tag.tag.ilike(f"%{q}%"))
        .order_by(Tag.tag)
        .limit(limit)
    )

    result = await db.execute(query)
    tags = result.scalars().all()

    return TagsResponseWrapper(tags=tags)


# Дополнительный эндпоинт для получения детальной информации о конкретном теге
@router.get("/{tag_name}", response_model=dict, summary="Получение информации о теге")
async def get_tag_info(
        tag_name: str,
        db: AsyncSession = Depends(get_db)
):
    """
    Получить детальную информацию о конкретном теге.

    - **tag_name**: название тега

    Возвращает информацию о теге: id, название, количество статей, дата создания.
    """
    # Находим тег по имени
    result = await db.execute(select(Tag).where(Tag.tag == tag_name))
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(404, f"Tag '{tag_name}' not found")

    # Подсчитываем количество статей с этим тегом
    articles_count_result = await db.execute(
        select(func.count()).select_from(ArticleTag).where(ArticleTag.tag_id == tag.id)
    )
    articles_count = articles_count_result.scalar() or 0

    return {
        "id": tag.id,
        "name": tag.tag,
        "articles_count": articles_count,
        "created_at": tag.created_at
    }
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models import Tag, ArticleTag
from app.schemas.wrappers import TagsResponseWrapper

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get(
    "",
    response_model=TagsResponseWrapper,
    summary="Получение всех тегов",
    description="Возвращает список всех тегов в системе",
    responses={
        200: {
            "description": "Список тегов",
            "content": {
                "application/json": {
                    "example": {
                        "tags": ["javascript", "python", "fastapi", "sqlalchemy"]
                    }
                }
            }
        }
    }
)
async def get_all_tags(db: AsyncSession = Depends(get_db)):
    """Получить список всех тегов в системе."""
    result = await db.execute(select(Tag.tag).order_by(Tag.tag))
    tags = result.scalars().all()

    return TagsResponseWrapper(tags=tags)


@router.get(
    "/popular",
    response_model=dict,
    summary="Получение популярных тегов",
    description="Возвращает теги, отсортированные по частоте использования",
    responses={
        200: {
            "description": "Популярные теги с количеством статей",
            "content": {
                "application/json": {
                    "example": {
                        "tags": [
                            {"name": "javascript", "count": 128},
                            {"name": "python", "count": 95},
                            {"name": "fastapi", "count": 42}
                        ]
                    }
                }
            }
        }
    }
)
async def get_popular_tags(
        min_count: int = Query(5, ge=1, description="Минимальное количество статей для включения в популярные"),
        db: AsyncSession = Depends(get_db)
):
    """Получить список популярных тегов с количеством статей."""
    query = (
        select(Tag.tag, func.count(ArticleTag.article_id).label('articles_count'))
        .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        .group_by(Tag.id, Tag.tag)
        .having(func.count(ArticleTag.article_id) >= min_count)
        .order_by(func.count(ArticleTag.article_id).desc())
    )

    result = await db.execute(query)
    popular_tags = [
        {"name": row[0], "count": row[1]}
        for row in result.all()
    ]

    return {"tags": popular_tags}
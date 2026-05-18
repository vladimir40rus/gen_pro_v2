from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.infra_external.connection_manager.db_connection import get_db_session
from app.infra_external.models.tag_db import TagDB, article_tag_association
from app.present.contracts.tag_contracts import TagsResponseWrapperContract

router = APIRouter(tags=["Tags"])


@router.get(
    "/tags",
    response_model=TagsResponseWrapperContract,
    summary="Получение всех тегов",
)
async def get_all_tags(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(TagDB.name).order_by(TagDB.name))
    tags = result.scalars().all()
    return TagsResponseWrapperContract(tags=tags)


@router.get(
    "/tags/popular",
    response_model=dict,
    summary="Получение популярных тегов",
)
async def get_popular_tags(
    min_count: int = Query(5, ge=1),
    db: AsyncSession = Depends(get_db_session)
):
    query = (
        select(TagDB.name, func.count(article_tag_association.c.article_id))
        .join(article_tag_association, TagDB.id == article_tag_association.c.tag_id)
        .group_by(TagDB.id)
        .having(func.count(article_tag_association.c.article_id) >= min_count)
        .order_by(func.count(article_tag_association.c.article_id).desc())
    )
    result = await db.execute(query)
    popular_tags = [{"name": row[0], "count": row[1]} for row in result.all()]
    return {"tags": popular_tags}
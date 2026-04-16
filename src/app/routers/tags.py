from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models import Tag
from app.schemas.tag import TagResponse

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", response_model=List[TagResponse], summary="Получить все теги")
async def get_all_tags(db: AsyncSession = Depends(get_db)):
    """Получить список всех тегов"""
    result = await db.execute(select(Tag).order_by(Tag.tag))
    tags = result.scalars().all()
    return tags
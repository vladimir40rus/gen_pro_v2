from typing import List
from pydantic import BaseModel, Field


class TagsResponseWrapperContract(BaseModel):
    """Обёртка для ответа со списком тегов"""
    tags: List[str] = Field(..., example=["javascript", "python", "fastapi"])


class PopularTagContract(BaseModel):
    """Популярный тег с количеством"""
    name: str = Field(..., example="javascript")
    count: int = Field(..., example=128)


class PopularTagsResponseContract(BaseModel):
    """Ответ с популярными тегами"""
    tags: List[PopularTagContract]
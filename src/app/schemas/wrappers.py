from typing import List, Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field

# Generic тип для переиспользования
T = TypeVar('T')

class SingleResponse(BaseModel, Generic[T]):
    """Базовая обертка для одного объекта"""
    data: T

class ListResponse(BaseModel, Generic[T]):
    """Базовая обертка для списка объектов"""
    items: List[T]
    total: int

# ========== Специфичные для API обертки ==========

class UserResponseWrapper(BaseModel):
    """Обертка для ответа с пользователем"""
    user: dict  # Временно используем dict, потом заменим на UserResponse

class ProfileResponseWrapper(BaseModel):
    """Обертка для ответа с профилем"""
    profile: dict

class ArticleResponseWrapper(BaseModel):
    """Обертка для ответа со статьей"""
    article: dict

class ArticlesResponseWrapper(BaseModel):
    """Обертка для ответа со списком статей"""
    articles: List[dict]
    articles_count: int = Field(..., ge=0, description="Общее количество статей")

class CommentResponseWrapper(BaseModel):
    """Обертка для ответа с комментарием"""
    comment: dict

class CommentsResponseWrapper(BaseModel):
    """Обертка для ответа со списком комментариев"""
    comments: List[dict]

class TagResponseWrapper(BaseModel):
    """Обертка для ответа с тегом"""
    tag: dict

class TagsResponseWrapper(BaseModel):
    """Обертка для ответа со списком тегов"""
    tags: List[str]
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ProfileContract(BaseModel):
    """Профиль пользователя (для вложения в статью)"""
    username: str = Field(..., example="johndoe")
    bio: Optional[str] = Field(None, example="Full-stack developer")
    image_url: Optional[str] = Field(None, example="https://storage.com/avatars/123.jpg")
    following: bool = Field(default=False, example=True)
    followers_count: int = Field(default=0, example=42)
    following_count: int = Field(default=0, example=15)
    articles_count: int = Field(default=0, example=7)


class ArticleBaseContract(BaseModel):
    """Базовый контракт статьи"""
    title: str = Field(..., min_length=3, max_length=100, example="How to Learn JavaScript in 2024")
    description: str = Field(..., min_length=10, max_length=255, example="A comprehensive guide to learning JavaScript")
    body: str = Field(..., min_length=50, example="JavaScript is one of the most popular programming languages...")
    slug: str = Field(..., min_length=1, max_length=100, pattern='^[a-z0-9-]+$', example="how-to-learn-javascript-in-2024")


class ArticleCreateContract(ArticleBaseContract):
    """Контракт для создания статьи"""
    tags: Optional[List[str]] = Field(None, max_length=10, example=["javascript", "programming", "webdev"])


class ArticleCreateWrapperContract(BaseModel):
    """Обёртка для создания статьи"""
    article: ArticleCreateContract


class ArticleUpdateContract(BaseModel):
    """Контракт для обновления статьи"""
    title: Optional[str] = Field(None, min_length=3, max_length=100, example="Updated Title")
    description: Optional[str] = Field(None, min_length=10, max_length=255, example="Updated description")
    body: Optional[str] = Field(None, min_length=50, example="Updated content...")
    slug: Optional[str] = Field(None, min_length=1, max_length=100, pattern='^[a-z0-9-]+$', example="updated-slug")


class ArticleUpdateWrapperContract(BaseModel):
    """Обёртка для обновления статьи"""
    article: ArticleUpdateContract


class ArticleResponseContract(BaseModel):
    """Контракт для ответа со статьёй"""
    id: int = Field(..., example=456)
    slug: str = Field(..., example="how-to-learn-javascript-in-2024")
    title: str = Field(..., example="How to Learn JavaScript in 2024")
    description: str = Field(..., example="A comprehensive guide to learning JavaScript")
    body: str = Field(..., example="JavaScript is one of the most popular programming languages...")
    author: ProfileContract
    tags: List[str] = Field(default_factory=list, example=["javascript"])
    favorited: bool = Field(default=False, example=True)
    favorites_count: int = Field(default=0, example=42)
    comments_count: int = Field(default=0, example=15)
    created_at: datetime = Field(..., example="2024-02-01T14:20:00Z")
    updated_at: Optional[datetime] = Field(None, example="2024-02-05T09:15:00Z")


class ArticleResponseWrapperContract(BaseModel):
    """Обёртка для ответа со статьёй"""
    article: ArticleResponseContract


class ArticlesResponseWrapperContract(BaseModel):
    """Обёртка для ответа со списком статей"""
    articles: List[ArticleResponseContract]
    articles_count: int = Field(..., example=100)
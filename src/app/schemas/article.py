import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ArticleBase(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Заголовок статьи",
        example="How to Learn JavaScript in 2024"
    )
    description: Optional[str] = Field(
        None,
        min_length=10,
        max_length=255,
        description="Краткое описание статьи",
        example="A comprehensive guide to learning JavaScript"
    )
    body: str = Field(
        ...,
        min_length=50,
        description="Основное содержание статьи",
        example="JavaScript is one of the most popular programming languages..."
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern='^[a-z0-9-]+$',
        description="Уникальный идентификатор для URL",
        example="how-to-learn-javascript-in-2024"
    )


class ArticleCreate(ArticleBase):
    tags: Optional[List[str]] = Field(
        None,
        max_length=10,
        description="Список тегов статьи",
        example=["javascript", "programming", "webdev"]
    )


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="Заголовок статьи",
        example="How to Learn JavaScript in 2024"
    )
    description: Optional[str] = Field(
        None,
        min_length=10,
        max_length=255,
        description="Краткое описание статьи",
        example="A comprehensive guide to learning JavaScript"
    )
    body: Optional[str] = Field(
        None,
        min_length=50,
        description="Основное содержание статьи",
        example="JavaScript is one of the most popular programming languages..."
    )
    slug: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        pattern='^[a-z0-9-]+$',
        description="Уникальный идентификатор для URL",
        example="how-to-learn-javascript-in-2024"
    )


class Profile(BaseModel):
    """Профиль пользователя (автора)"""
    username: str = Field(..., description="Имя пользователя", example="john_doe")
    bio: Optional[str] = Field(None, description="О себе", example="Software developer")
    image: Optional[str] = Field(None, description="URL аватара", example="https://example.com/avatar.jpg")

    model_config = ConfigDict(from_attributes=True)


class ArticleResponse(ArticleBase):
    id: int = Field(..., description="ID статьи", example=456)
    author: Profile = Field(..., description="Автор статьи")
    tags: List[str] = Field(
        default_factory=list,
        description="Список тегов статьи",
        example=["javascript", "programming"]
    )
    favorited: bool = Field(
        default=False,
        description="Добавил ли текущий пользователь статью в избранное",
        example=True
    )
    favorites_count: int = Field(
        default=0,
        ge=0,
        description="Количество лайков статьи",
        example=42
    )
    comments_count: int = Field(
        default=0,
        ge=0,
        description="Количество комментариев",
        example=15
    )
    created_at: datetime.datetime = Field(
        ...,
        description="Дата создания",
        example="2024-02-01T14:20:00Z"
    )
    updated_at: Optional[datetime.datetime] = Field(
        None,
        description="Дата последнего обновления",
        example="2024-02-05T09:15:00Z"
    )

    model_config = ConfigDict(from_attributes=True)


class MultipleArticlesResponse(BaseModel):
    """Ответ со списком статей"""
    articles: List[ArticleResponse] = Field(..., description="Список статей")
    articles_count: int = Field(..., ge=0, description="Общее количество статей", example=100)
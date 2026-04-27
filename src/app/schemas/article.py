import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ArticleBase(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Заголовок статьи",
        examples=["How to Learn JavaScript in 2024"]
    )
    description: Optional[str] = Field(
        None,
        min_length=10,
        max_length=255,
        description="Краткое описание статьи",
        examples=["A comprehensive guide to learning JavaScript"]
    )
    body: str = Field(
        ...,
        min_length=50,
        description="Основное содержание статьи",
        examples=["JavaScript is one of the most popular programming languages..."]
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern='^[a-z0-9-]+$',
        description="Уникальный идентификатор для URL",
        examples=["how-to-learn-javascript-in-2024"]
    )


class ArticleCreate(ArticleBase):
    tags: Optional[List[str]] = Field(
        None,
        max_length=10,
        description="Список тегов статьи",
        examples=[["javascript", "programming", "webdev"]]
    )


class ArticleCreateWrapper(BaseModel):
    """Обертка для создания статьи (соответствует OpenAPI)"""
    article: ArticleCreate

    model_config = ConfigDict(from_attributes=True)


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="Заголовок статьи",
        examples=["Updated Title"]
    )
    description: Optional[str] = Field(
        None,
        min_length=10,
        max_length=255,
        description="Краткое описание статьи",
        examples=["Updated description"]
    )
    body: Optional[str] = Field(
        None,
        min_length=50,
        description="Основное содержание статьи",
        examples=["Updated content..."]
    )
    slug: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        pattern='^[a-z0-9-]+$',
        description="Уникальный идентификатор для URL",
        examples=["updated-slug"]
    )


class ArticleUpdateWrapper(BaseModel):
    """Обертка для обновления статьи (соответствует OpenAPI)"""
    article: ArticleUpdate

    model_config = ConfigDict(from_attributes=True)


class AuthorProfile(BaseModel):
    """Профиль автора (соответствует OpenAPI)"""
    username: str = Field(..., description="Имя пользователя", examples=["johndoe"])
    bio: Optional[str] = Field(None, description="О себе", examples=["Full-stack developer"])
    image_url: Optional[str] = Field(None, description="URL аватара", examples=["https://storage.com/avatars/123.jpg"])
    following: bool = Field(default=False, description="Подписан ли текущий пользователь", examples=[True])
    followers_count: int = Field(default=0, description="Количество подписчиков", examples=[42])
    following_count: int = Field(default=0, description="Количество подписок", examples=[15])
    articles_count: int = Field(default=0, description="Количество статей", examples=[7])

    model_config = ConfigDict(from_attributes=True)


class ArticleResponse(BaseModel):
    """Ответ со статьей (соответствует OpenAPI)"""
    id: int = Field(..., description="ID статьи", examples=[456])
    slug: str = Field(..., description="Уникальный идентификатор для URL", examples=["how-to-learn-javascript-in-2024"])
    title: str = Field(..., description="Заголовок статьи", examples=["How to Learn JavaScript in 2024"])
    description: str = Field(..., description="Краткое описание статьи", examples=["A comprehensive guide to learning JavaScript"])
    body: str = Field(..., description="Основное содержание статьи", examples=["JavaScript is one of the most popular programming languages..."])
    author: AuthorProfile = Field(..., description="Автор статьи")
    tags: List[str] = Field(
        default_factory=list,
        description="Список тегов статьи",
        examples=[["javascript"]]
    )
    favorited: bool = Field(
        default=False,
        description="Добавил ли текущий пользователь статью в избранное",
        examples=[True]
    )
    favorites_count: int = Field(
        default=0,
        ge=0,
        description="Количество лайков статьи",
        examples=[42]
    )
    comments_count: int = Field(
        default=0,
        ge=0,
        description="Количество комментариев",
        examples=[15]
    )
    created_at: datetime.datetime = Field(
        ...,
        description="Дата создания",
        examples=["2024-02-01T14:20:00Z"]
    )
    updated_at: Optional[datetime.datetime] = Field(
        None,
        description="Дата последнего обновления",
        examples=["2024-02-05T09:15:00Z"]
    )

    model_config = ConfigDict(from_attributes=True)


class MultipleArticlesResponse(BaseModel):
    """Ответ со списком статей"""
    articles: List[ArticleResponse] = Field(..., description="Список статей")
    articles_count: int = Field(..., ge=0, description="Общее количество статей", examples=[100])
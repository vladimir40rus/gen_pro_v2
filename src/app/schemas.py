import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        json_schema_extra={"пример": "Джон"}
    )


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        json_schema_extra={"example": "strongpassword"}
    )
    email: EmailStr = Field(
        ...,
        json_schema_extra={"example": "user@example.com"}
    )


class UserResponse(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime.datetime


# ========== МОДЕЛИ ДЛЯ СТАТЕЙ ==========
class ArticleBase(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        json_schema_extra={"example": "Моя первая статья"}
    )
    description: str | None = Field(
        None,
        max_length=500,
        json_schema_extra={"example": "Краткое описание статьи"}
    )
    body: str = Field(
        ...,
        json_schema_extra={"example": "Полный текст статьи..."}
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        json_schema_extra={"example": "Моя первая статья"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Моя первая статья",
                "description": "Краткое описание статьи",
                "body": "Полный текст статьи...",
                "slug": "первая статья"
            }
        }
    )


class ArticleCreate(ArticleBase):
    author_id: int = Field(
        ...,
        gt=0,
        json_schema_extra={"example": 1}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Моя первая статья",
                "description": "Краткое описание статьи",
                "body": "Полный текст статьи...",
                "slug": "Первая статья",
                "author_id": 1
            }
        }
    )


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    body: str | None = None
    slug: str | None = Field(None, min_length=1, max_length=100)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Обновленное название",
                "description": "Обновленное описание"
            }
        }
    )

class ArticleResponse(ArticleBase):
    id: int
    author_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


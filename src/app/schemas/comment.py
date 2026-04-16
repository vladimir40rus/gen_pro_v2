import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CommentBase(BaseModel):
    body: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Текст комментария",
        example="Great article! Very helpful."
    )


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    body: Optional[str] = Field(None, min_length=1, max_length=500, description="Текст комментария")


class Author(BaseModel):
    """Автор комментария"""
    username: str = Field(..., description="Имя пользователя", example="john_doe")
    bio: Optional[str] = Field(None, description="О себе")
    image: Optional[str] = Field(None, description="URL аватара")

    model_config = ConfigDict(from_attributes=True)


class CommentResponse(CommentBase):
    id: int = Field(..., description="ID комментария", example=1)
    author: Author = Field(..., description="Автор комментария")
    created_at: datetime.datetime = Field(..., description="Дата создания", example="2024-02-01T14:20:00Z")
    updated_at: Optional[datetime.datetime] = Field(None, description="Дата обновления")

    model_config = ConfigDict(from_attributes=True)


class MultipleCommentsResponse(BaseModel):
    """Ответ со списком комментариев"""
    comments: list[CommentResponse] = Field(..., description="Список комментариев")
    comments_count: int = Field(..., ge=0, description="Общее количество комментариев", example=50)
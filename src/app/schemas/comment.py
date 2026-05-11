import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CommentBase(BaseModel):
    body: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Текст комментария",
        examples=["Great article! Very helpful."]
    )


class CommentCreate(CommentBase):
    pass


class CommentCreateWrapper(BaseModel):
    """Обертка для создания комментария (соответствует OpenAPI)"""
    comment: CommentCreate

    model_config = ConfigDict(from_attributes=True)


class CommentUpdate(BaseModel):
    body: Optional[str] = Field(None, min_length=1, max_length=1000, description="Текст комментария", examples=["Updated comment text."])


class CommentUpdateWrapper(BaseModel):
    """Обертка для обновления комментария (соответствует OpenAPI)"""
    comment: CommentUpdate

    model_config = ConfigDict(from_attributes=True)


class AuthorProfile(BaseModel):
    """Автор комментария (соответствует OpenAPI)"""
    username: str = Field(..., description="Имя пользователя", examples=["johndoe"])
    bio: Optional[str] = Field(None, description="О себе", examples=["Full-stack developer"])
    image_url: Optional[str] = Field(None, description="URL аватара", examples=["https://storage.com/avatars/123.jpg"])
    following: bool = Field(default=False, description="Подписан ли текущий пользователь", examples=[True])
    followers_count: int = Field(default=0, description="Количество подписчиков", examples=[42])
    following_count: int = Field(default=0, description="Количество подписок", examples=[15])
    articles_count: int = Field(default=0, description="Количество статей", examples=[7])

    model_config = ConfigDict(from_attributes=True)


class CommentResponse(BaseModel):
    """Ответ с комментарием (соответствует OpenAPI)"""
    id: int = Field(..., description="ID комментария", examples=[789])
    body: str = Field(..., description="Текст комментария", examples=["Great article! Very helpful."])
    author: AuthorProfile = Field(..., description="Автор комментария")
    article_id: int = Field(..., description="ID статьи", examples=[456])
    created_at: datetime.datetime = Field(..., description="Дата создания", examples=["2024-02-02T10:30:00Z"])
    updated_at: Optional[datetime.datetime] = Field(None, description="Дата обновления", examples=["2024-02-02T11:15:00Z"])

    model_config = ConfigDict(from_attributes=True)


class MultipleCommentsResponse(BaseModel):
    """Ответ со списком комментариев"""
    comments: list[CommentResponse] = Field(..., description="Список комментариев")
    comments_count: int = Field(..., ge=0, description="Общее количество комментариев", examples=[50])
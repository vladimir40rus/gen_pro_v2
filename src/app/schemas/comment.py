import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CommentBase(BaseModel):
    body: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Текст комментария",
        examples=["Great article! Very helpful."]
    )
    model_config = ConfigDict(from_attributes=True)


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    body: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Текст комментария",
        examples=["Updated comment text."]
    )


class CreateCommentRequest(BaseModel):
    """Обёртка для создания комментария"""
    comment: CommentCreate = Field(..., description="Данные комментария")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comment": {
                    "body": "Great article! Very helpful."
                }
            }
        }
    )


class UpdateCommentRequest(BaseModel):
    """Обёртка для обновления комментария"""
    comment: CommentUpdate = Field(..., description="Данные для обновления комментария")


class Author(BaseModel):
    """Автор комментария"""
    username: str = Field(..., description="Имя пользователя", examples=["johndoe"])
    bio: Optional[str] = Field(None, description="О себе", examples=["Full-stack developer"])
    image_url: Optional[str] = Field(None, description="URL аватара", examples=["https://storage.com/avatars/123.jpg"])
    following: bool = Field(False, description="Подписан ли текущий пользователь", examples=[True])
    followers_count: int = Field(0, ge=0, description="Количество подписчиков", examples=[42])
    following_count: int = Field(0, ge=0, description="Количество подписок", examples=[15])
    articles_count: int = Field(0, ge=0, description="Количество статей", examples=[7])

    model_config = ConfigDict(from_attributes=True)


class CommentResponse(BaseModel):
    """Ответ с комментарием"""
    id: int = Field(..., description="ID комментария", examples=[789])
    body: str = Field(..., min_length=1, max_length=500, description="Текст комментария",
                      examples=["Great article! Very helpful."])
    author: Author = Field(..., description="Автор комментария")
    article_id: int = Field(..., description="ID статьи", examples=[456])
    created_at: datetime.datetime = Field(..., description="Дата создания", examples=["2024-02-02T10:30:00Z"])
    updated_at: Optional[datetime.datetime] = Field(None, description="Дата обновления",
                                                    examples=["2024-02-02T11:15:00Z"])

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 789,
                "body": "Great article! Very helpful.",
                "author": {
                    "username": "johndoe",
                    "bio": "Full-stack developer",
                    "image_url": "https://storage.com/avatars/123.jpg",
                    "following": True,
                    "followers_count": 42,
                    "following_count": 15,
                    "articles_count": 7
                },
                "article_id": 456,
                "created_at": "2024-02-02T10:30:00Z",
                "updated_at": "2024-02-02T11:15:00Z"
            }
        }
    )


class CommentResponseWrapper(BaseModel):
    """Обёртка для ответа с одним комментарием"""
    comment: CommentResponse = Field(..., description="Комментарий")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comment": {
                    "id": 789,
                    "body": "Great article! Very helpful.",
                    "author": {
                        "username": "johndoe",
                        "bio": "Full-stack developer",
                        "image_url": "https://storage.com/avatars/123.jpg",
                        "following": True,
                        "followers_count": 42,
                        "following_count": 15,
                        "articles_count": 7
                    },
                    "article_id": 456,
                    "created_at": "2024-02-02T10:30:00Z",
                    "updated_at": "2024-02-02T11:15:00Z"
                }
            }
        }
    )


class CommentsResponseWrapper(BaseModel):
    """Обёртка для ответа со списком комментариев"""
    comments: list[CommentResponse] = Field(..., description="Список комментариев")
    comments_count: int = Field(..., ge=0, description="Общее количество комментариев")


class MultipleCommentsResponse(BaseModel):
    """Ответ со списком комментариев"""
    comments: list[CommentResponse] = Field(..., description="Список комментариев")
    comments_count: int = Field(..., ge=0, description="Общее количество комментариев", examples=[50])
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AuthorContract(BaseModel):
    """Автор комментария"""
    username: str = Field(..., example="johndoe")
    bio: Optional[str] = Field(None, example="Full-stack developer")
    image_url: Optional[str] = Field(None, example="https://storage.com/avatars/123.jpg")
    following: bool = Field(default=False, example=True)
    followers_count: int = Field(default=0, example=42)
    following_count: int = Field(default=0, example=15)
    articles_count: int = Field(default=0, example=7)


class CommentBaseContract(BaseModel):
    """Базовый контракт комментария"""
    body: str = Field(..., min_length=1, max_length=1000, example="Great article! Very helpful.")


class CommentCreateContract(CommentBaseContract):
    pass


class CommentCreateWrapperContract(BaseModel):
    """Обёртка для создания комментария"""
    comment: CommentCreateContract


class CommentUpdateContract(BaseModel):
    """Контракт для обновления комментария"""
    body: Optional[str] = Field(None, min_length=1, max_length=1000)


class CommentUpdateWrapperContract(BaseModel):
    """Обёртка для обновления комментария"""
    comment: CommentUpdateContract


class CommentResponseContract(CommentBaseContract):
    """Контракт для ответа с комментарием"""
    id: int = Field(..., example=789)
    author: AuthorContract
    article_id: int = Field(..., example=456)
    created_at: datetime = Field(..., example="2024-02-02T10:30:00Z")
    updated_at: Optional[datetime] = Field(None, example="2024-02-02T11:15:00Z")


class CommentResponseWrapperContract(BaseModel):
    """Обёртка для ответа с комментарием"""
    comment: CommentResponseContract


class CommentsResponseWrapperContract(BaseModel):
    """Обёртка для ответа со списком комментариев"""
    comments: List[CommentResponseContract]
from typing import Optional
from pydantic import BaseModel, Field


class ProfileContract(BaseModel):
    """Публичный профиль пользователя"""
    username: str = Field(..., example="johndoe")
    bio: Optional[str] = Field(None, example="Full-stack developer")
    image_url: Optional[str] = Field(None, example="https://storage.com/avatars/123.jpg")
    following: bool = Field(default=False, example=True)
    followers_count: int = Field(default=0, example=42)
    following_count: int = Field(default=0, example=15)
    articles_count: int = Field(default=0, example=7)


class ProfileResponseWrapperContract(BaseModel):
    """Обёртка для ответа с профилем"""
    profile: ProfileContract


class FollowResponseContract(BaseModel):
    """Ответ при подписке/отписке"""
    profile: ProfileContract
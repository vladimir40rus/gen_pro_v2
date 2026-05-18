# src/app/present/contracts/user_contracts.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserBaseContract(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, example="johndoe")
    email: EmailStr = Field(..., example="john@example.com")


class UserCreateContract(UserBaseContract):
    password: str = Field(..., min_length=8, example="SecurePass123")


class UserCreateWrapperContract(BaseModel):
    user: UserCreateContract


class UserResponseContract(BaseModel):
    id: int = Field(..., example=123)
    username: str = Field(..., example="johndoe")
    email: EmailStr = Field(..., example="john@example.com")
    bio: Optional[str] = Field(None, example="Full-stack developer and tech writer")
    image_url: Optional[str] = Field(None, example="https://storage.com/avatars/123.jpg")
    created_at: datetime = Field(..., example="2024-01-15T10:30:00Z")
    updated_at: Optional[datetime] = Field(None, example="2024-02-20T15:45:00Z")

    class Config:
        from_attributes = True


class UserResponseWrapperContract(BaseModel):
    user: UserResponseContract


class LoginRequestContract(BaseModel):
    email: EmailStr = Field(..., example="john@example.com")
    password: str = Field(..., example="SecurePass123")


class LoginRequestWrapperContract(BaseModel):
    user: LoginRequestContract


class UserUpdateContract(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=30, example="johndoe_updated")
    email: Optional[EmailStr] = Field(None, example="john.new@example.com")
    bio: Optional[str] = Field(None, max_length=500, example="Updated bio")
    image_url: Optional[str] = Field(None, example="https://storage.com/avatars/123-new.jpg")


class UserUpdateWrapperContract(BaseModel):
    user: UserUpdateContract


class UserStatsContract(BaseModel):
    """Статистика пользователя"""
    username: str
    articles_published: int = 0
    total_views: int = 0
    total_likes_received: int = 0
    total_comments_received: int = 0
    followers_count: int = 0
    following_count: int = 0
    joined_date: str
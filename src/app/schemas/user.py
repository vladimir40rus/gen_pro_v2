import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="Имя пользователя",
        example="john_doe"
    )


class UserCreate(UserBase):
    email: EmailStr = Field(
        ...,
        description="Email пользователя",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Пароль",
        example="strongpassword123",
        writeOnly=True
    )


class UserResponse(UserBase):
    id: int = Field(..., description="ID пользователя", example=1)
    email: EmailStr = Field(..., description="Email пользователя", example="user@example.com")
    bio: Optional[str] = Field(None, description="О себе", example="Software developer")
    image: Optional[str] = Field(None, description="URL аватара", example="https://example.com/avatar.jpg")
    created_at: datetime.datetime = Field(..., description="Дата регистрации", example="2024-02-01T14:20:00Z")

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=20, description="Имя пользователя")
    email: Optional[EmailStr] = Field(None, description="Email пользователя")
    password: Optional[str] = Field(None, min_length=8, description="Пароль", writeOnly=True)
    bio: Optional[str] = Field(None, max_length=500, description="О себе")
    image: Optional[str] = Field(None, max_length=500, description="URL аватара")

    model_config = ConfigDict(from_attributes=True)


class Profile(BaseModel):
    """Профиль пользователя (для отображения)"""
    username: str = Field(..., description="Имя пользователя", example="john_doe")
    bio: Optional[str] = Field(None, description="О себе", example="Software developer")
    image: Optional[str] = Field(None, description="URL аватара", example="https://example.com/avatar.jpg")
    following: bool = Field(default=False, description="Подписан ли текущий пользователь", example=False)

    model_config = ConfigDict(from_attributes=True)
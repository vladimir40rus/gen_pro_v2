import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Имя пользователя",
        examples=["john_doe"]
    )


class UserCreate(UserBase):
    email: EmailStr = Field(
        ...,
        description="Email пользователя",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Пароль (минимум 8 символов)",
        examples=["strongpassword123"],
        writeOnly=True
    )


class UserCreateWrapper(BaseModel):
    """Обертка для создания пользователя"""
    user: UserCreate

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Ответ с данными пользователя"""
    id: int = Field(..., description="ID пользователя", examples=[123])
    username: str = Field(..., description="Имя пользователя", examples=["john_doe"])
    email: EmailStr = Field(..., description="Email пользователя", examples=["john@example.com"])
    bio: Optional[str] = Field(None, description="Информация о пользователе", examples=["Full-stack developer and tech writer"])
    image_url: Optional[str] = Field(None, description="URL аватара пользователя", examples=["https://storage.com/avatars/123.jpg"])
    created_at: datetime.datetime = Field(..., description="Дата регистрации", examples=["2024-01-15T10:30:00Z"])
    updated_at: Optional[datetime.datetime] = Field(None, description="Дата последнего обновления", examples=["2024-02-20T15:45:00Z"])

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Обновление данных пользователя (все поля опциональны)"""
    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=30,
        description="Имя пользователя",
        examples=["johndoe_updated"]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Email пользователя",
        examples=["john.new@example.com"]
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=72,
        description="Пароль",
        writeOnly=True
    )
    bio: Optional[str] = Field(
        None,
        max_length=500,
        description="Информация о пользователе",
        examples=["Updated bio"]
    )
    image_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL аватара",
        examples=["https://storage.com/avatars/123-new.jpg"]
    )

    model_config = ConfigDict(from_attributes=True)


class UserUpdateWrapper(BaseModel):
    """Обертка для обновления пользователя"""
    user: UserUpdate

    model_config = ConfigDict(from_attributes=True)


class Profile(BaseModel):
    """Публичный профиль пользователя"""
    username: str = Field(..., description="Имя пользователя", examples=["john_doe"])
    bio: Optional[str] = Field(None, description="Информация о пользователе", examples=["Full-stack developer"])
    image_url: Optional[str] = Field(None, description="URL аватара", examples=["https://storage.com/avatars/123.jpg"])
    following: bool = Field(default=False, description="Подписан ли текущий пользователь", examples=[True])

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    """Обертка для профиля"""
    profile: Profile

    model_config = ConfigDict(from_attributes=True)
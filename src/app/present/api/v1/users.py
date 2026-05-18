from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra_external.connection_manager.db_connection import get_db_session
from app.infra_external.models.user_db import UserDB
from app.infra_external.models.article_db import ArticleDB
from app.infra_external.models.follower_db import FollowerDB
from app.present.api.v1.contracts.user_contracts import (
    UserCreateWrapperContract,
    UserResponseWrapperContract,
    UserUpdateWrapperContract,
    LoginRequestWrapperContract,
)

router = APIRouter(tags=["Users", "Authentication"])


# Вспомогательная функция для форматирования пользователя
def format_user(user: UserDB) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "bio": user.bio,
        "image_url": user.image_url,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }


# Вспомогательная функция для получения текущего пользователя (временно)
async def get_current_user(db: AsyncSession) -> UserDB:
    result = await db.execute(select(UserDB).order_by(UserDB.id).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found. Please create a user first.")
    return user


# ========== Регистрация ==========
@router.post(
    "/users",
    response_model=UserResponseWrapperContract,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя и возвращает JWT токен",
    responses={
        201: {
            "description": "Пользователь успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": 123,
                            "username": "johndoe",
                            "email": "john@example.com",
                            "bio": "Full-stack developer and tech writer",
                            "image_url": "https://storage.com/avatars/123.jpg",
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-02-20T15:45:00Z"
                        }
                    }
                }
            }
        },
        422: {
            "description": "Ошибка валидации (email или username уже заняты)",
            "content": {
                "application/json": {
                    "example": {
                        "errors": {
                            "email": ["can't be blank", "is invalid"],
                            "password": ["is too short (minimum is 8 characters)"]
                        }
                    }
                }
            }
        },
        429: {
            "description": "Too Many Requests",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Rate limit exceeded. Try again later."
                    }
                }
            }
        }
    }
)
async def create_user(
        create_data: UserCreateWrapperContract,
        db: AsyncSession = Depends(get_db_session)
):
    user_data = create_data.user
    errors = {}

    # Проверка username
    existing = await db.execute(select(UserDB).where(UserDB.username == user_data.username))
    if existing.scalar_one_or_none():
        errors["username"] = ["already exists"]

    # Проверка email
    existing = await db.execute(select(UserDB).where(UserDB.email == user_data.email))
    if existing.scalar_one_or_none():
        errors["email"] = ["already exists"]

    # Проверка пароля
    if len(user_data.password) < 8:
        errors["password"] = ["is too short (minimum is 8 characters)"]

    if errors:
        return JSONResponse(status_code=422, content={"errors": errors})

    user = UserDB(
        username=user_data.username,
        email=user_data.email,
        password_hash=user_data.password,
        bio=None,
        image_url=None
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # TODO: Добавить JWT токен
    # token = create_access_token({"sub": user.id})

    return UserResponseWrapperContract(user=format_user(user))


# ========== Логин ==========
@router.post(
    "/users/login",
    response_model=UserResponseWrapperContract,
    status_code=status.HTTP_200_OK,
    summary="Аутентификация пользователя",
    description="Проверяет credentials и возвращает JWT токен",
    responses={
        200: {
            "description": "Успешная аутентификация",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": 123,
                            "username": "johndoe",
                            "email": "john@example.com",
                            "bio": "Full-stack developer and tech writer",
                            "image_url": "https://storage.com/avatars/123.jpg",
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-02-20T15:45:00Z"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Неверный email или пароль",
            "content": {
                "application/json": {
                    "example": {
                        "errors": {
                            "email": ["is invalid"],
                            "password": ["is incorrect"]
                        }
                    }
                }
            }
        },
        429: {
            "description": "Too Many Requests",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Too many failed attempts. Try again in 15 minutes."
                    }
                }
            }
        }
    }
)
async def login(
        login_data: LoginRequestWrapperContract,
        db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(UserDB).where(UserDB.email == login_data.user.email))
    user = result.scalar_one_or_none()

    if not user or user.password_hash != login_data.user.password:
        return JSONResponse(
            status_code=401,
            content={"errors": {"email": ["is invalid"], "password": ["is incorrect"]}}
        )

    # TODO: Добавить JWT токен
    # token = create_access_token({"sub": user.id})

    return UserResponseWrapperContract(user=format_user(user))


# ========== Текущий пользователь ==========
@router.get(
    "/user",
    response_model=UserResponseWrapperContract,
    summary="Получение текущего пользователя",
    responses={
        200: {
            "description": "Информация о пользователе",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": 123,
                            "username": "johndoe",
                            "email": "john@example.com",
                            "bio": "Full-stack developer and tech writer",
                            "image_url": "https://storage.com/avatars/123.jpg",
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-02-20T15:45:00Z"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Authentication required"
                    }
                }
            }
        }
    }
)
async def get_current_user_info(
        db: AsyncSession = Depends(get_db_session)
):
    user = await get_current_user(db)
    return UserResponseWrapperContract(user=format_user(user))


# ========== Обновление профиля ==========
@router.put(
    "/user",
    response_model=UserResponseWrapperContract,
    summary="Обновление профиля",
    responses={
        200: {
            "description": "Профиль обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": 123,
                            "username": "johndoe",
                            "email": "john@example.com",
                            "bio": "Full-stack developer and tech writer",
                            "image_url": "https://storage.com/avatars/123.jpg",
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-02-20T15:45:00Z"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Authentication required"
                    }
                }
            }
        },
        422: {
            "description": "Ошибка валидации",
            "content": {
                "application/json": {
                    "example": {
                        "errors": {
                            "username": ["already exists"],
                            "email": ["already exists"]
                        }
                    }
                }
            }
        }
    }
)
async def update_user(
        update_data: UserUpdateWrapperContract,
        db: AsyncSession = Depends(get_db_session)
):
    current_user = await get_current_user(db)
    user_data = update_data.user
    errors = {}

    if user_data.username is not None:
        if user_data.username != current_user.username:
            existing = await db.execute(select(UserDB).where(UserDB.username == user_data.username))
            if existing.scalar_one_or_none():
                errors["username"] = ["already exists"]
            else:
                current_user.username = user_data.username

    if user_data.email is not None:
        if user_data.email != current_user.email:
            existing = await db.execute(select(UserDB).where(UserDB.email == user_data.email))
            if existing.scalar_one_or_none():
                errors["email"] = ["already exists"]
            else:
                current_user.email = user_data.email

    if user_data.bio is not None:
        current_user.bio = user_data.bio

    if user_data.image_url is not None:
        current_user.image_url = user_data.image_url

    if errors:
        return JSONResponse(status_code=422, content={"errors": errors})

    await db.commit()
    await db.refresh(current_user)

    return UserResponseWrapperContract(user=format_user(current_user))


# ========== Статистика пользователя ==========
@router.get(
    "/stats/user/{username}",
    summary="Статистика пользователя",
    responses={
        200: {
            "description": "Статистика пользователя",
            "content": {
                "application/json": {
                    "example": {
                        "username": "johndoe",
                        "articles_published": 7,
                        "total_views": 0,
                        "total_likes_received": 42,
                        "total_comments_received": 15,
                        "followers_count": 10,
                        "following_count": 7,
                        "joined_date": "2024-01-15"
                    }
                }
            }
        },
        404: {
            "description": "Пользователь не найден",
            "content": {
                "application/json": {
                    "example": {
                        "error": "User not found"
                    }
                }
            }
        }
    }
)
async def get_user_stats(
        username: str = Path(..., description="Имя пользователя", examples=["johndoe"]),
        db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(UserDB).where(UserDB.username == username))
    user = result.scalar_one_or_none()

    if not user:
        return JSONResponse(status_code=404, content={"error": f"User '{username}' not found"})

    # Количество статей
    articles_count = await db.execute(select(func.count()).select_from(ArticleDB).where(ArticleDB.author_id == user.id))

    # Количество подписчиков
    followers_count = await db.execute(
        select(func.count()).select_from(FollowerDB).where(FollowerDB.following_id == user.id))

    # Количество подписок
    following_count = await db.execute(
        select(func.count()).select_from(FollowerDB).where(FollowerDB.follower_id == user.id))

    return {
        "username": user.username,
        "articles_published": articles_count.scalar() or 0,
        "total_views": 0,
        "total_likes_received": 0,
        "total_comments_received": 0,
        "followers_count": followers_count.scalar() or 0,
        "following_count": following_count.scalar() or 0,
        "joined_date": user.created_at.strftime("%Y-%m-%d") if user.created_at else "2024-01-15"
    }
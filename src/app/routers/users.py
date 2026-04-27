from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Favorite, Comment, Article, Follower
from app.schemas.user import UserCreate, UserCreateWrapper, UserResponse, UserUpdate, UserUpdateWrapper
from app.schemas.wrappers import UserResponseWrapper, ProfileResponseWrapper, UserData

router = APIRouter(prefix="", tags=["Users"])


class UserStats(BaseModel):
    """Статистика пользователя (соответствует OpenAPI)"""
    username: str
    articles_published: int = 0
    total_views: int = 0
    total_likes_received: int = 0
    total_comments_received: int = 0
    followers_count: int = 0
    following_count: int = 0
    joined_date: str


async def get_current_user(db: AsyncSession = Depends(get_db)):
    """Получить текущего пользователя (первого в таблице)"""
    result = await db.execute(select(User).order_by(User.id).limit(1))
    user = result.scalar_one_or_none()

    if not user:
        return JSONResponse(
            status_code=404,
            content={"error": "User not found. Please create a user first."}
        )

    return user


def format_user_response(user: User) -> UserData:
    """Форматирует пользователя для ответа"""
    return UserData(
        id=user.id,
        username=user.username,
        email=user.email,
        bio=user.bio,
        image_url=user.image_url,
        created_at=user.created_at.isoformat() if user.created_at else None,
        updated_at=user.updated_at.isoformat() if user.updated_at else None
    )


# ========== Регистрация ==========
@router.post(
    "/users",
    response_model=UserResponseWrapper,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
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
                            "bio": None,
                            "image_url": None,
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": None
                        }
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
async def create_user(create_data: UserCreateWrapper, db: AsyncSession = Depends(get_db)):
    """Создать нового пользователя"""
    user_data = create_data.user
    errors = {}

    # Валидация username
    if not user_data.username or len(user_data.username) < 3:
        errors["username"] = ["must be at least 3 characters"]
    else:
        existing = await db.execute(select(User).where(User.username == user_data.username))
        if existing.scalar_one_or_none():
            errors["username"] = ["already exists"]

    # Валидация email
    if not user_data.email:
        errors["email"] = ["can't be blank"]
    else:
        existing = await db.execute(select(User).where(User.email == user_data.email))
        if existing.scalar_one_or_none():
            errors["email"] = ["already exists"]

    # Валидация пароля
    if not user_data.password:
        errors["password"] = ["can't be blank"]
    elif len(user_data.password) < 8:
        errors["password"] = ["is too short (minimum is 8 characters)"]

    # Если есть ошибки
    if errors:
        return JSONResponse(
            status_code=422,
            content={"errors": errors}
        )

    # Создаем пользователя
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=user_data.password,
        bio=None,
        image_url=None
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponseWrapper(user=format_user_response(user))


# ========== Текущий пользователь ==========
@router.get(
    "/user",
    response_model=UserResponseWrapper,
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
            "description": "Не аутентифицирован"
        }
    }
)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    if isinstance(current_user, JSONResponse):
        return current_user
    return UserResponseWrapper(user=format_user_response(current_user))


@router.put(
    "/user",
    response_model=UserResponseWrapper,
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
            "description": "Не аутентифицирован"
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
        update_data: UserUpdateWrapper,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Обновить текущего пользователя"""

    if isinstance(current_user, JSONResponse):
        return current_user

    user_data = update_data.user
    errors = {}

    if user_data.username is not None:
        if len(user_data.username) < 3:
            errors["username"] = ["must be at least 3 characters"]
        elif user_data.username != current_user.username:
            existing = await db.execute(
                select(User).where(User.username == user_data.username)
            )
            if existing.scalar_one_or_none():
                errors["username"] = ["already exists"]
            else:
                current_user.username = user_data.username

    if user_data.email is not None:
        if user_data.email != current_user.email:
            existing = await db.execute(
                select(User).where(User.email == user_data.email)
            )
            if existing.scalar_one_or_none():
                errors["email"] = ["already exists"]
            else:
                current_user.email = user_data.email

    if user_data.password is not None:
        if len(user_data.password) < 8:
            errors["password"] = ["is too short (minimum is 8 characters)"]
        else:
            current_user.password_hash = user_data.password

    if user_data.bio is not None:
        current_user.bio = user_data.bio

    if user_data.image_url is not None:
        current_user.image_url = user_data.image_url

    if errors:
        return JSONResponse(
            status_code=422,
            content={"errors": errors}
        )

    await db.commit()
    await db.refresh(current_user)

    return UserResponseWrapper(user=format_user_response(current_user))


# ========== Статистика ==========
@router.get(
    "/stats/user/{username}",
    response_model=UserStats,
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
            "description": "Пользователь не найден"
        }
    }
)
async def get_user_stats(username: str, db: AsyncSession = Depends(get_db)):
    """Получить статистику пользователя по username"""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        return JSONResponse(
            status_code=404,
            content={"error": f"User '{username}' not found"}
        )

    # Количество статей
    articles_count_result = await db.execute(
        select(func.count()).select_from(Article).where(Article.author_id == user.id)
    )
    articles_published = articles_count_result.scalar() or 0

    # Количество комментариев на статьях пользователя
    total_comments_received = await db.execute(
        select(func.count())
        .select_from(Comment)
        .join(Article, Comment.article_id == Article.id)
        .where(Article.author_id == user.id)
    )
    total_comments_received = total_comments_received.scalar() or 0

    # Количество лайков на статьях пользователя
    total_likes_received_result = await db.execute(
        select(func.count())
        .select_from(Favorite)
        .join(Article, Favorite.article_id == Article.id)
        .where(Article.author_id == user.id)
    )
    total_likes_received = total_likes_received_result.scalar() or 0

    # Количество подписчиков
    followers_count_result = await db.execute(
        select(func.count()).select_from(Follower).where(Follower.following_id == user.id)
    )
    followers_count = followers_count_result.scalar() or 0

    # Количество подписок
    following_count_result = await db.execute(
        select(func.count()).select_from(Follower).where(Follower.follower_id == user.id)
    )
    following_count = following_count_result.scalar() or 0

    # Дата регистрации
    joined_date = user.created_at.strftime("%Y-%m-%d") if user.created_at else "2024-01-15"

    return UserStats(
        username=user.username,
        articles_published=articles_published,
        total_views=0,
        total_likes_received=total_likes_received,
        total_comments_received=total_comments_received,
        followers_count=followers_count,
        following_count=following_count,
        joined_date=joined_date
    )
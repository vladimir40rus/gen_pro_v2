from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models import User, Follower, Article
from app.schemas.wrappers import ProfileResponseWrapper, ProfileData

router = APIRouter(prefix="/profiles", tags=["Profile"])


async def get_current_user(db: AsyncSession) -> Optional[User]:
    """Временно получить текущего пользователя (первого в таблице)"""
    result = await db.execute(select(User).order_by(User.id).limit(1))
    return result.scalar_one_or_none()


async def get_profile_data(username: str, current_user_id: Optional[int] = None, db: AsyncSession = None) -> dict:
    """Получить данные профиля"""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        return None

    followers_count = await db.execute(
        select(func.count()).select_from(Follower).where(Follower.following_id == user.id)
    )

    following_count = await db.execute(
        select(func.count()).select_from(Follower).where(Follower.follower_id == user.id)
    )

    articles_count = await db.execute(
        select(func.count()).select_from(Article).where(Article.author_id == user.id)
    )

    following = False
    if current_user_id:
        follow_result = await db.execute(
            select(Follower).where(
                Follower.follower_id == current_user_id,
                Follower.following_id == user.id
            )
        )
        following = follow_result.scalar_one_or_none() is not None

    return {
        "username": user.username,
        "bio": user.bio,
        "image_url": user.image_url,
        "following": following,
        "followers_count": followers_count.scalar() or 0,
        "following_count": following_count.scalar() or 0,
        "articles_count": articles_count.scalar() or 0
    }


@router.get(
    "/{username}",
    response_model=ProfileResponseWrapper,
    summary="Получение профиля пользователя",
    description="Возвращает публичный профиль пользователя по username",
    responses={
        200: {
            "description": "Профиль найден",
            "content": {
                "application/json": {
                    "example": {
                        "profile": {
                            "username": "johndoe",
                            "bio": "Full-stack developer",
                            "image_url": "https://storage.com/avatars/123.jpg",
                            "following": True,
                            "followers_count": 42,
                            "following_count": 15,
                            "articles_count": 7
                        }
                    }
                }
            }
        },
        404: {"description": "Пользователь не найден"}
    }
)
async def get_profile(
        username: str = Path(..., description="Имя пользователя", examples=["johndoe"]),
        db: AsyncSession = Depends(get_db)
):
    """Получить публичный профиль пользователя"""
    current_user = await get_current_user(db)
    current_user_id = current_user.id if current_user else None

    profile_data = await get_profile_data(username, current_user_id, db)

    if not profile_data:
        return JSONResponse(
            status_code=404,
            content={"error": "User not found"}
        )

    profile = ProfileData(**profile_data)
    return ProfileResponseWrapper(profile=profile)


@router.post(
    "/{username}/follow",
    response_model=ProfileResponseWrapper,
    status_code=status.HTTP_200_OK,
    summary="Подписаться на пользователя",
    description="Добавляет подписку на указанного пользователя",
    responses={
        200: {
            "description": "Успешно подписан",
            "content": {
                "application/json": {
                    "example": {
                        "profile": {
                            "username": "johndoe",
                            "bio": "Full-stack developer",
                            "image_url": "https://storage.com/avatars/123.jpg",
                            "following": True,
                            "followers_count": 43,
                            "following_count": 15,
                            "articles_count": 7
                        }
                    }
                }
            }
        },
        400: {"description": "Нельзя подписаться на себя"},
        401: {"description": "Не аутентифицирован"},
        404: {"description": "Пользователь не найден"}
    }
)
async def follow_user(
        username: str = Path(..., description="Имя пользователя", examples=["johndoe"]),
        db: AsyncSession = Depends(get_db)
):
    """Подписаться на пользователя"""

    current_user = await get_current_user(db)
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    result = await db.execute(select(User).where(User.username == username))
    following = result.scalar_one_or_none()
    if not following:
        return JSONResponse(
            status_code=404,
            content={"error": "User not found"}
        )

    if current_user.id == following.id:
        return JSONResponse(
            status_code=400,
            content={"error": "Cannot follow yourself"}
        )

    existing = await db.execute(
        select(Follower).where(
            Follower.follower_id == current_user.id,
            Follower.following_id == following.id
        )
    )
    if existing.scalar_one_or_none():
        profile_data = await get_profile_data(username, current_user.id, db)
        profile = ProfileData(**profile_data)
        return ProfileResponseWrapper(profile=profile)

    follow = Follower(follower_id=current_user.id, following_id=following.id)
    db.add(follow)
    await db.commit()

    profile_data = await get_profile_data(username, current_user.id, db)
    profile = ProfileData(**profile_data)

    return ProfileResponseWrapper(profile=profile)


@router.delete(
    "/{username}/follow",
    response_model=ProfileResponseWrapper,
    status_code=status.HTTP_200_OK,
    summary="Отписаться от пользователя",
    description="Удаляет подписку на указанного пользователя",
    responses={
        200: {
            "description": "Успешно отписан",
            "content": {
                "application/json": {
                    "example": {
                        "profile": {
                            "username": "johndoe",
                            "bio": "Full-stack developer",
                            "image_url": "https://storage.com/avatars/123.jpg",
                            "following": False,
                            "followers_count": 41,
                            "following_count": 15,
                            "articles_count": 7
                        }
                    }
                }
            }
        },
        401: {"description": "Не аутентифицирован"},
        404: {"description": "Пользователь не найден"}
    }
)
async def unfollow_user(
        username: str = Path(..., description="Имя пользователя", examples=["johndoe"]),
        db: AsyncSession = Depends(get_db)
):
    """Отписаться от пользователя"""

    current_user = await get_current_user(db)
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    result = await db.execute(select(User).where(User.username == username))
    following = result.scalar_one_or_none()
    if not following:
        return JSONResponse(
            status_code=404,
            content={"error": "User not found"}
        )

    follow_result = await db.execute(
        select(Follower).where(
            Follower.follower_id == current_user.id,
            Follower.following_id == following.id
        )
    )
    follow = follow_result.scalar_one_or_none()

    if not follow:
        profile_data = await get_profile_data(username, current_user.id, db)
        profile = ProfileData(**profile_data)
        return ProfileResponseWrapper(profile=profile)

    await db.delete(follow)
    await db.commit()

    profile_data = await get_profile_data(username, current_user.id, db)
    profile = ProfileData(**profile_data)

    return ProfileResponseWrapper(profile=profile)
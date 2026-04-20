from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Favorite, Comment, Article, Follower
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserUpdateWrapper
from app.schemas.wrappers import UserResponseWrapper, ProfileResponseWrapper

router = APIRouter(prefix="/users", tags=["Users"])


class UserStats(BaseModel):
    username: str
    articles_count: int = 0
    comments_count: int = 0
    favorites_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    total_likes_received: int = 0


async def get_current_user(db: AsyncSession = Depends(get_db)):
    """Получить текущего пользователя (первого в таблице)"""
    result = await db.execute(select(User).order_by(User.id).limit(1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "No users found. Please create a user first.")

    return user


@router.post("/", response_model=UserResponseWrapper, summary="Регистрация нового пользователя")
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Создать нового пользователя"""
    existing = await db.execute(select(User).where(User.username == user_data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Username already exists")

    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already exists")

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

    user_response = UserResponse(
        username=user.username,
        email=user.email,
        bio=user.bio,
        image_url=user.image_url
    )

    return UserResponseWrapper(user=user_response.model_dump())


@router.put("/", response_model=UserResponseWrapper, summary="Обновление профиля")
async def update_user(
        update_data: UserUpdateWrapper,  # ← ОБЕРТКА
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Обновить текущего пользователя"""

    user_data = update_data.user  # ← ДОСТАЁМ ДАННЫЕ

    if user_data.username is not None:
        if user_data.username != current_user.username:
            existing = await db.execute(
                select(User).where(User.username == user_data.username)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(400, "Username already exists")
            current_user.username = user_data.username

    if user_data.email is not None:
        if user_data.email != current_user.email:
            existing = await db.execute(
                select(User).where(User.email == user_data.email)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(400, "Email already exists")
            current_user.email = user_data.email

    if user_data.password is not None:
        current_user.password_hash = user_data.password

    if user_data.bio is not None:
        current_user.bio = user_data.bio

    if user_data.image_url is not None:
        current_user.image_url = user_data.image_url

    await db.commit()
    await db.refresh(current_user)

    user_response = UserResponse(
        username=current_user.username,
        email=current_user.email,
        bio=current_user.bio,
        image_url=current_user.image_url
    )

    return UserResponseWrapper(user=user_response.model_dump())


@router.get("/", response_model=UserResponseWrapper, summary="Получить текущего пользователя")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    user_response = UserResponse(
        username=current_user.username,
        email=current_user.email,
        bio=current_user.bio,
        image_url=current_user.image_url
    )
    return UserResponseWrapper(user=user_response.model_dump())


@router.get("/profile/{username}", response_model=ProfileResponseWrapper, summary="Получить публичный профиль")
async def get_profile(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "User not found")

    profile = {
        "username": user.username,
        "bio": user.bio,
        "image_url": user.image_url,
        "following": False
    }

    return ProfileResponseWrapper(profile=profile)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT, summary="Удаление текущего пользователя")
async def delete_current_user(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    await db.delete(current_user)
    await db.commit()


@router.get("/stats/{username}", response_model=UserStats, summary="Получить статистику пользователя")
async def get_user_stats(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, f"User '{username}' not found")

    articles_count_result = await db.execute(
        select(func.count()).select_from(Article).where(Article.author_id == user.id)
    )
    articles_count = articles_count_result.scalar() or 0

    comments_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.author_id == user.id)
    )
    comments_count = comments_count_result.scalar() or 0

    favorites_count_result = await db.execute(
        select(func.count()).select_from(Favorite).where(Favorite.user_id == user.id)
    )
    favorites_count = favorites_count_result.scalar() or 0

    followers_count_result = await db.execute(
        select(func.count()).select_from(Follower).where(Follower.following_id == user.id)
    )
    followers_count = followers_count_result.scalar() or 0

    following_count_result = await db.execute(
        select(func.count()).select_from(Follower).where(Follower.follower_id == user.id)
    )
    following_count = following_count_result.scalar() or 0

    total_likes_received_result = await db.execute(
        select(func.count())
        .select_from(Favorite)
        .join(Article, Favorite.article_id == Article.id)
        .where(Article.author_id == user.id)
    )
    total_likes_received = total_likes_received_result.scalar() or 0

    return UserStats(
        username=user.username,
        articles_count=articles_count,
        comments_count=comments_count,
        favorites_count=favorites_count,
        followers_count=followers_count,
        following_count=following_count,
        total_likes_received=total_likes_received
    )
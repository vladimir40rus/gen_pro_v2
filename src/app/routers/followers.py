from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models import Follower, User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/followers", tags=["Followers"])


@router.post("/", summary="Подписаться на пользователя")
async def follow_user(
        follower_id: int,
        following_id: int,
        db: AsyncSession = Depends(get_db)
):
    # Проверяем, существуют ли пользователи
    follower = await db.get(User, follower_id)
    following = await db.get(User, following_id)
    if not follower or not following:
        raise HTTPException(404, "User not found")
    """Подписаться на пользователя"""
    if follower_id == following_id:
        raise HTTPException(400, "Cannot follow yourself")

    # Проверяем, не подписан ли уже
    existing = await db.execute(
        select(Follower).where(
            Follower.follower_id == follower_id,
            Follower.following_id == following_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already following this user")

    # Подписываем
    follow = Follower(follower_id=follower_id, following_id=following_id)
    db.add(follow)
    await db.commit()
    return {"message": f"User {follower_id} now follows {following_id}"}


@router.delete("/", summary="Отписаться от пользователя")
async def unfollow_user(
        follower_id: int,
        following_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Отписаться от пользователя"""
    result = await db.execute(
        select(Follower).where(
            Follower.follower_id == follower_id,
            Follower.following_id == following_id
        )
    )
    follow = result.scalar_one_or_none()

    if not follow:
        raise HTTPException(404, "Follow relationship not found")

    await db.delete(follow)
    await db.commit()
    return {"message": f"User {follower_id} unfollowed {following_id}"}


@router.get("/followers/{user_id}", response_model=List[UserResponse],summary="Получить подписчиков пользователя")
async def get_followers(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить подписчиков пользователя"""
    query = (
        select(User)
        .join(Follower, User.id == Follower.follower_id)
        .where(Follower.following_id == user_id)
    )
    result = await db.execute(query)
    return result.scalars().all()


from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra_external.connection_manager.db_connection import get_db_session
from app.infra_external.models.user_db import UserDB
from app.infra_external.models.follower_db import FollowerDB
from app.infra_external.models.article_db import ArticleDB

router = APIRouter(tags=["Profile"])


async def get_current_user(db: AsyncSession) -> UserDB:
    result = await db.execute(select(UserDB).order_by(UserDB.id).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.get(
    "/profiles/{username}",
    summary="Получение профиля пользователя",
)
async def get_profile(
    username: str = Path(..., description="Имя пользователя", examples=["johndoe"]),
    db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(UserDB).where(UserDB.username == username))
    user = result.scalar_one_or_none()
    if not user:
        return JSONResponse(status_code=404, content={"error": "User not found"})

    followers_count = await db.execute(select(func.count()).select_from(FollowerDB).where(FollowerDB.following_id == user.id))
    following_count = await db.execute(select(func.count()).select_from(FollowerDB).where(FollowerDB.follower_id == user.id))
    articles_count = await db.execute(select(func.count()).select_from(ArticleDB).where(ArticleDB.author_id == user.id))

    return {
        "profile": {
            "username": user.username,
            "bio": user.bio,
            "image_url": user.image_url,
            "following": False,
            "followers_count": followers_count.scalar() or 0,
            "following_count": following_count.scalar() or 0,
            "articles_count": articles_count.scalar() or 0
        }
    }


@router.post(
    "/profiles/{username}/follow",
    status_code=status.HTTP_200_OK,
    summary="Подписаться на пользователя",
)
async def follow_user(
    username: str,
    db: AsyncSession = Depends(get_db_session)
):
    current_user = await get_current_user(db)
    result = await db.execute(select(UserDB).where(UserDB.username == username))
    following = result.scalar_one_or_none()
    if not following:
        return JSONResponse(status_code=404, content={"error": "User not found"})

    if current_user.id == following.id:
        return JSONResponse(status_code=400, content={"error": "Cannot follow yourself"})

    existing = await db.execute(
        select(FollowerDB).where(
            FollowerDB.follower_id == current_user.id,
            FollowerDB.following_id == following.id
        )
    )
    if existing.scalar_one_or_none():
        return JSONResponse(status_code=400, content={"error": "Already following"})

    follow = FollowerDB(follower_id=current_user.id, following_id=following.id)
    db.add(follow)
    await db.commit()

    return {"message": f"Now following {username}"}


@router.delete(
    "/profiles/{username}/follow",
    status_code=status.HTTP_200_OK,
    summary="Отписаться от пользователя",
)
async def unfollow_user(
    username: str,
    db: AsyncSession = Depends(get_db_session)
):
    current_user = await get_current_user(db)
    result = await db.execute(select(UserDB).where(UserDB.username == username))
    following = result.scalar_one_or_none()
    if not following:
        return JSONResponse(status_code=404, content={"error": "User not found"})

    follow = await db.execute(
        select(FollowerDB).where(
            FollowerDB.follower_id == current_user.id,
            FollowerDB.following_id == following.id
        )
    )
    follow = follow.scalar_one_or_none()
    if not follow:
        return JSONResponse(status_code=404, content={"error": "Not following"})

    await db.delete(follow)
    await db.commit()

    return {"message": f"Unfollowed {username}"}
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Favorite, Comment, Article, Follower
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

# Схема для статистики пользователя (ДОБАВЛЕНА)
class UserStats(BaseModel):
    username: str
    articles_count: int = 0
    comments_count: int = 0
    favorites_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    total_likes_received: int = 0


# Функция для получения текущего пользователя (первого в таблице)
async def get_current_user(db: AsyncSession = Depends(get_db)):
    """Получить текущего пользователя (первого в таблице)"""
    result = await db.execute(select(User).order_by(User.id).limit(1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "No users found. Please create a user first.")

    return user

@router.get("/", response_model=UserResponse, summary="Получить текущего пользователя")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
@router.post("/", response_model=UserResponse, summary="Регистрация нового пользователя")
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Создать нового пользователя"""
    # Проверяем уникальность username
    existing = await db.execute(select(User).where(User.username == user_data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Username already exists")

    # Проверяем уникальность email
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already exists")

    # Создаем пользователя (пароль сохраняем как есть, без хэширования)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=user_data.password  # ⚠️ ВНИМАНИЕ: пароль в открытом виде!
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/stats/{username}", response_model=UserStats, summary="Получить статистику пользователя")
async def get_user_stats(username: str, db: AsyncSession = Depends(get_db)):
    """Получить статистику пользователя по username"""

    # Находим пользователя
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, f"User '{username}' not found")

    # Количество статей пользователя
    articles_count_result = await db.execute(
        select(func.count()).select_from(Article).where(Article.author_id == user.id)
    )
    articles_count = articles_count_result.scalar() or 0

    # Количество комментариев пользователя
    comments_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.author_id == user.id)
    )
    comments_count = comments_count_result.scalar() or 0

    # Количество избранных статей пользователя
    favorites_count_result = await db.execute(
        select(func.count()).select_from(Favorite).where(Favorite.user_id == user.id)
    )
    favorites_count = favorites_count_result.scalar() or 0

    # Количество подписчиков пользователя
    followers_count_result = await db.execute(
        select(func.count()).select_from(Follower).where(Follower.following_id == user.id)
    )
    followers_count = followers_count_result.scalar() or 0

    # Количество подписок пользователя
    following_count_result = await db.execute(
        select(func.count()).select_from(Follower).where(Follower.follower_id == user.id)
    )
    following_count = following_count_result.scalar() or 0

    # Общее количество лайков на всех статьях пользователя
    # Считаем количество записей в Favorite, где article_id принадлежит статьям пользователя
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


@router.put("/", response_model=UserResponse, summary="Обновление профиля")
async def update_user(
        user_data: UserUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Обновить текущего пользователя (первого в БД)"""

    # Обновляем только переданные поля
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

    if user_data.image is not None:
        current_user.image_url = user_data.image

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT, summary="Удаление текущего пользователя")
async def delete_current_user(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Удалить текущего пользователя (первого в БД)"""
    await db.delete(current_user)
    await db.commit()





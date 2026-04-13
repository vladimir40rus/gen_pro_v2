from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
router = APIRouter(prefix="/Users", tags=["Управление профилем и пользователем"])

@router.post("/", response_model=UserResponse, tags=["Регистрация нового пользователя"])
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Создать нового пользователя"""
    # Проверяем, не существует ли уже такой пользователь
    existing = await db.execute(select(User).where(User.username == user_data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Создаем пользователя (в реальном проекте хешируйте пароль!)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=user_data.password  # ⚠️ Временно, нужно хешировать!
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    """Получить всех пользователей"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users



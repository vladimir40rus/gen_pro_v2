from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def get_users(db: AsyncSession = Depends(get_db)):
    """Получить всех пользователей"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@router.post("/")
async def create_user(username: str, email: str, password: str, db: AsyncSession = Depends(get_db)):
    """Создать нового пользователя"""
    user = User(
        username=username,
        email=email,
        password_hash=password  # В реальном проекте нужно хешировать
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
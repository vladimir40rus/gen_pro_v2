from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base
from app.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/create-tables")
async def create_tables():
    """Создает все таблицы в БД (только для разработки!)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return {"message": "✅ Tables created successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/drop-tables")
async def drop_tables():
    """⚠️ УДАЛЯЕТ все таблицы (только для разработки!)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        return {"message": "❌ Tables dropped successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-db")
async def reset_database():
    """Полный сброс БД (удалить и создать заново)"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        return {"message": "🔄 Database reset successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# src/app/present/api/v1/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.infra_external.connection_manager.db_connection import engine
from app.infra_external.database.init_db import create_tables, drop_tables, reset_tables

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/create-tables", summary="Создать все таблицы")
async def create_all_tables():
    """Создает все таблицы в базе данных (только для разработки!)"""
    try:
        await create_tables(engine)
        return {"message": "✅ Tables created successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drop-tables", summary="Удалить все таблицы")
async def drop_all_tables():
    """⚠️ УДАЛЯЕТ все таблицы (только для разработки!)"""
    try:
        await drop_tables(engine)
        return {"message": "❌ Tables dropped successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-db", summary="Сбросить базу данных")
async def reset_database():
    """Полный сброс БД (удалить и создать заново)"""
    try:
        await reset_tables(engine)
        return {"message": "🔄 Database reset successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
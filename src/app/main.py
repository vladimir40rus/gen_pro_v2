import uvicorn
from fastapi import FastAPI
from app.database import Base, engine
from app.routers import users
import app.models
import asyncio
from app.routers import users, admin


app = FastAPI(title="Мой проект на фастапи!")


app.include_router(users.router)
app.include_router(admin.router)




# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == "__main__": #Для докер хост используем нули
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"

    )
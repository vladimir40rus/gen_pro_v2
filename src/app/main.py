from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from app.database import engine, Base
from app.routers import users


# Создаём таблицы при запуске


app = FastAPI()

# Подключаем роутеры
app.include_router(users.router)

# Простая проверка
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/users")
async def get_users():
    return [{"id": 1, "name": "Vladimir"}, {"id": 2, "name": "Stanislav"}]


# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == "__main__": #Для докер хост используем нули
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"

    )
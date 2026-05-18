import uvicorn
import logging
from fastapi import FastAPI
from app.present.routs import group_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание приложения FastAPI
app = FastAPI(
    title="Blog Platform API",
    description="RESTful API для блоговой платформы с луковой архитектурой",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Подключение всех роутеров
app.include_router(group_router)

# Простой эндпоинт для проверки работоспособности
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "API работает!"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
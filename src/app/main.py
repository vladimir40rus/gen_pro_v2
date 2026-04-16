import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers import users, admin, articles, comments, tags, favorites, followers

app = FastAPI(title="Мой проект на фастапи!")

# Подключаем статические файлы на /static (не на /)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path), html=True), name="static")
app.include_router(users)
app.include_router(admin)
app.include_router(articles)
app.include_router(comments)
app.include_router(tags)
app.include_router(favorites)
app.include_router(followers)

# Добавляем корневой эндпоинт для редиректа на фронтенд
@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static")

# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == "__main__": #Для докер хост используем нули
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"

    )
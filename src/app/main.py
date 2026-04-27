import uvicorn
from fastapi import FastAPI

from app.routers import users, admin, articles, comments, tags, favorites, followers

app = FastAPI(title="Мой проект на фастапи!")


app.include_router(users)
app.include_router(admin)
app.include_router(articles)
app.include_router(comments)
app.include_router(tags)
app.include_router(favorites)
app.include_router(followers)


# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == "__main__": #Для докер хост используем нули
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"

    )
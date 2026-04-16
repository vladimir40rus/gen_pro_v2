from app.routers.users import router as users
from app.routers.admin import router as admin
from app.routers.articles import router as articles
from app.routers.comments import router as comments
from app.routers.tags import router as tags
from app.routers.favorites import router as favorites
from app.routers.followers import router as followers

__all__ = [
    "users",
    "admin",
    "articles",
    "comments",
    "tags",
    "favorites",
    "followers",
]
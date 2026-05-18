from .users import router as users_router
from .articles import router as articles_router
from .comments import router as comments_router
from .tags import router as tags_router
from .favorites import router as favorites_router
from .profiles import router as profiles_router
from .admin import router as admin_router  # ← добавить

__all__ = [
    "users_router",
    "articles_router",
    "comments_router",
    "tags_router",
    "favorites_router",
    "profiles_router",
    "admin_router",
]
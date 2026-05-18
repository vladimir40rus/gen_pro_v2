from fastapi import APIRouter
from app.present.api.v1 import (
    users_router,
    articles_router,
    comments_router,
    tags_router,
    favorites_router,
    profiles_router,
)

group_router = APIRouter()

group_router.include_router(users_router, prefix="/api/v1", tags=["Users"])
group_router.include_router(articles_router, prefix="/api/v1", tags=["Articles", "Feed"])
group_router.include_router(comments_router, prefix="/api/v1", tags=["Comments"])
group_router.include_router(tags_router, prefix="/api/v1", tags=["Tags"])
group_router.include_router(favorites_router, prefix="/api/v1", tags=["Favorites"])
group_router.include_router(profiles_router, prefix="/api/v1", tags=["Profile"])
from app.schemas.user import UserBase, UserCreate, UserResponse, UserUpdate
from app.schemas.article import ArticleBase, ArticleCreate, ArticleUpdate, ArticleResponse
from app.schemas.comment import CommentBase, CommentCreate, CommentResponse, CommentUpdate
from app.schemas.tag import TagBase, TagCreate, TagResponse
from app.schemas.wrappers import (
    UserResponseWrapper,
    ProfileResponseWrapper,
    ArticleResponseWrapper,
    ArticlesResponseWrapper,
    CommentResponseWrapper,
    CommentsResponseWrapper,
    TagResponseWrapper,
    TagsResponseWrapper
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "ArticleBase",
    "ArticleCreate",
    "ArticleUpdate",
    "ArticleResponse",
    "CommentBase",
    "CommentCreate",
    "CommentResponse",
    "CommentUpdate",
    "TagBase",
    "TagCreate",
    "TagResponse",
    # Добавленные обертки
    "UserResponseWrapper",
    "ProfileResponseWrapper",
    "ArticleResponseWrapper",
    "ArticlesResponseWrapper",
    "CommentResponseWrapper",
    "CommentsResponseWrapper",
    "TagResponseWrapper",
    "TagsResponseWrapper"
]
from typing import List, Optional
from pydantic import BaseModel, Field

# ========== Обертки для пользователей ==========

class UserData(BaseModel):
    """Данные пользователя"""
    id: int
    username: str
    email: str
    bio: Optional[str] = None
    image_url: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

class UserResponseWrapper(BaseModel):
    """Обертка для ответа с пользователем"""
    user: UserData

# ========== Обертки для профиля ==========

class ProfileData(BaseModel):
    """Данные профиля"""
    username: str
    bio: Optional[str] = None
    image_url: Optional[str] = None
    following: bool = False

class ProfileResponseWrapper(BaseModel):
    """Обертка для ответа с профилем"""
    profile: ProfileData

# ========== Обертки для статей ==========

class ArticleData(BaseModel):
    """Данные статьи"""
    id: int
    title: str
    description: str
    body: str
    slug: str
    author: dict
    tags: List[str]
    favorited: bool
    favorites_count: int
    comments_count: int
    created_at: str
    updated_at: Optional[str] = None

class ArticleResponseWrapper(BaseModel):
    """Обертка для ответа со статьей"""
    article: ArticleData

class ArticlesResponseWrapper(BaseModel):
    """Обертка для ответа со списком статей"""
    articles: List[ArticleData]
    articles_count: int

# ========== Обертки для комментариев ==========

class AuthorData(BaseModel):
    """Данные автора комментария"""
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None

class CommentData(BaseModel):
    """Данные комментария"""
    id: int
    body: str
    author: AuthorData
    created_at: str
    updated_at: Optional[str] = None

class CommentResponseWrapper(BaseModel):
    """Обертка для ответа с комментарием"""
    comment: CommentData

class CommentsResponseWrapper(BaseModel):
    """Обертка для ответа со списком комментариев"""
    comments: List[CommentData]

# ========== Обертки для тегов ==========

class TagData(BaseModel):
    """Данные тега"""
    id: int
    name: str
    created_at: Optional[str] = None

class TagResponseWrapper(BaseModel):
    """Обертка для ответа с тегом"""
    tag: TagData

class TagsResponseWrapper(BaseModel):
    """Обертка для ответа со списком тегов"""
    tags: List[str]
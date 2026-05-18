from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Any


@dataclass
class ArticleCreateDTO:
    """DTO для создания статьи"""
    title: str
    description: str
    body: str
    slug: str
    author_id: int
    tags: Optional[List[str]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ArticleUpdateDTO:
    """DTO для обновления статьи"""
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    slug: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AuthorDTO:
    """DTO для автора статьи"""
    username: str
    bio: Optional[str]
    image_url: Optional[str]
    following: bool = False
    followers_count: int = 0
    following_count: int = 0
    articles_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ArticleResponseDTO:
    """DTO для ответа со статьёй"""
    id: int
    slug: str
    title: str
    description: str
    body: str
    author: AuthorDTO
    tags: List[str]
    favorited: bool
    favorites_count: int
    comments_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    def to_dict(self) -> dict[str, Any]:
        result = {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "body": self.body,
            "author": self.author.to_dict(),
            "tags": self.tags,
            "favorited": self.favorited,
            "favorites_count": self.favorites_count,
            "comments_count": self.comments_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return result
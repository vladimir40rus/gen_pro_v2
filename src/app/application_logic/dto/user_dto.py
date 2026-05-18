from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any


@dataclass
class UserCreateDTO:
    """DTO для создания пользователя"""
    username: str
    email: str
    password: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UserResponseDTO:
    """DTO для ответа с данными пользователя"""
    id: int
    username: str
    email: str
    bio: Optional[str]
    image_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        if result.get('created_at'):
            result['created_at'] = result['created_at'].isoformat()
        if result.get('updated_at'):
            result['updated_at'] = result['updated_at'].isoformat()
        return result


@dataclass
class UserUpdateDTO:
    """DTO для обновления пользователя"""
    username: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class UserStatsDTO:
    """DTO для статистики пользователя"""
    username: str
    articles_published: int
    total_likes_received: int
    total_comments_received: int
    followers_count: int
    following_count: int
    joined_date: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
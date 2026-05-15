from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class User:
    """Доменная сущность пользователя"""
    id: Optional[int]
    username: str
    email: str
    password_hash: str
    bio: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(self.password_hash) < 8:
            raise ValueError("Password too short")

    def follow(self, target_id: int) -> dict:
        """Подписаться на пользователя"""
        if self.id == target_id:
            raise ValueError("Cannot follow yourself")
        return {"follower_id": self.id, "following_id": target_id}

    def update_profile(self, username: str = None, bio: str = None, image_url: str = None):
        if username:
            self.username = username
        if bio is not None:
            self.bio = bio
        if image_url is not None:
            self.image_url = image_url
        self.updated_at = datetime.now()
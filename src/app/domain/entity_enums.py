from enum import Enum


class ArticleStatus(str, Enum):
    """Статус статьи"""
    PUBLISHED = "published"
    DRAFT = "draft"
    ARCHIVED = "archived"


class FollowStatus(str, Enum):
    """Статус подписки"""
    FOLLOWING = "following"
    BLOCKED = "blocked"
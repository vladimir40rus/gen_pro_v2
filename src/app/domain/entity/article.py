from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Article:
    """Доменная сущность статьи"""
    id: Optional[int]
    title: str
    description: str
    body: str
    slug: str
    author_id: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if len(self.title) < 3:
            raise ValueError("Title must be at least 3 characters")
        if not self.slug.replace('-', '').isalnum():
            raise ValueError("Invalid slug format")

    def update(self, title: str = None, description: str = None,
               body: str = None, slug: str = None):
        if title:
            self.title = title
        if description is not None:
            self.description = description
        if body:
            self.body = body
        if slug:
            self.slug = slug
        self.updated_at = datetime.now()

    def is_author(self, user_id: int) -> bool:
        return self.author_id == user_id
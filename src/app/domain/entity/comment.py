from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Comment:
    """Доменная сущность комментария"""
    id: Optional[int]
    body: str
    article_id: int
    author_id: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if len(self.body) < 1:
            raise ValueError("Comment cannot be empty")
        if len(self.body) > 1000:
            raise ValueError("Comment too long")

    def update(self, new_body: str):
        if len(new_body) < 1:
            raise ValueError("Comment cannot be empty")
        self.body = new_body
        self.updated_at = datetime.now()
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Tag:
    """Доменная сущность тега"""
    id: Optional[int]
    name: str
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if len(self.name) < 1:
            raise ValueError("Tag name cannot be empty")
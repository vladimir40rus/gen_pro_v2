import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CommentBase(BaseModel):
    body: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Текст комментария",
        example="Great article! Very helpful."
    )

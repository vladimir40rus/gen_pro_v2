import datetime
from pydantic import BaseModel, Field, ConfigDict


class TagBase(BaseModel):
    tag: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern='^[a-z0-9-]+$',
        description="Название тега",
        example="javascript"
    )


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: int = Field(..., description="ID тега", example=1)
    created_at: datetime.datetime = Field(..., description="Дата создания", example="2024-02-01T14:20:00Z")

    model_config = ConfigDict(from_attributes=True)
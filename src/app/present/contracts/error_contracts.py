from typing import Dict, List, Any
from pydantic import BaseModel, Field


class ErrorContract(BaseModel):
    """Контракт для ошибок валидации"""
    errors: Dict[str, List[str]] = Field(
        ...,
        example={
            "email": ["can't be blank", "is invalid"],
            "password": ["is too short (minimum is 8 characters)"]
        }
    )


class SimpleErrorContract(BaseModel):
    """Контракт для простых ошибок"""
    error: str = Field(..., example="Article not found")
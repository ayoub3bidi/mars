from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RunCreate(BaseModel):
    prompt: str = Field(min_length=1, max_length=10000)
    token_budget: int | None = None


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    result: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime

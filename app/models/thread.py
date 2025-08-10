import datetime
import uuid
from enum import Enum
from typing import Any

from sqlalchemy import JSON, DateTime, func
from sqlmodel import Column, Field, SQLModel


class ThreadStatus(Enum):
    idle = "idle"
    busy = "busy"
    interrupted = "interrupted"
    error = "error"


class Thread(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
    )
    updated_at: datetime.datetime = Field(
        sa_column=Column(DateTime(), onupdate=func.now())
    )
    user_id: str = Field(
        description="The ID of the user that owns this thread.",
    )
    agent_id: str = Field(
        description="The ID of the agent that owns this thread.",
    )
    meta: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: ThreadStatus | None = Field(
        default=ThreadStatus.idle,
        description="Thread status to filter on.",
        title="Thread Status",
    )

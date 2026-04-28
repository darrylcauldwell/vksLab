"""Task model for SDDC Manager API responses."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Task(BaseModel):
    """SDDC Manager task response model."""

    id: str = Field(description="Task ID")
    status: TaskStatus = Field(description="Task status")
    progress: Optional[int] = Field(default=None, description="Progress percentage")
    description: Optional[str] = Field(default=None, description="Task description")
    message: Optional[str] = Field(default=None, description="Task message")
    errors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Error details",
    )
    sub_tasks: Optional[List["Task"]] = Field(
        default=None,
        alias="subTasks",
        description="Nested subtasks",
    )
    creation_time_millis: Optional[int] = Field(
        default=None,
        alias="creationTimeMillis",
        description="Task creation timestamp (ms)",
    )
    start_time_millis: Optional[int] = Field(
        default=None,
        alias="startTimeMillis",
        description="Task start timestamp (ms)",
    )
    end_time_millis: Optional[int] = Field(
        default=None,
        alias="endTimeMillis",
        description="Task end timestamp (ms)",
    )

    model_config = ConfigDict(populate_by_name=True, use_enum_values=False)

    @property
    def is_terminal(self) -> bool:
        """Check if task is in terminal state."""
        return self.status in (
            TaskStatus.SUCCESSFUL,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )

    @property
    def is_successful(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.SUCCESSFUL

    @property
    def is_failed(self) -> bool:
        """Check if task failed."""
        return self.status in (TaskStatus.FAILED, TaskStatus.CANCELLED)


# Update forward references
Task.model_rebuild()

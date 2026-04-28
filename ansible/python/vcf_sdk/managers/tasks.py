"""Task polling and monitoring."""

import logging
import time

from vcf_sdk.exceptions import TaskFailedError, TimeoutError
from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import Task

logger = logging.getLogger(__name__)


class TaskManager(BaseManager):
    """Task polling and monitoring."""

    def get(self, task_id: str) -> Task:
        """Get task status by ID."""
        response = self._get(f"/v1/tasks/{task_id}")
        return Task(**response)

    def retry(self, task_id: str) -> Task:
        """Retry a failed task."""
        response = self._patch(f"/v1/tasks/{task_id}")
        return Task(**response)

    def cancel(self, task_id: str) -> None:
        """Cancel a running task."""
        self._delete(f"/v1/tasks/{task_id}")

    def wait_for_completion(
        self,
        task_id: str,
        timeout: int = 3600,
        poll_interval: int = 30,
    ) -> Task:
        """
        Wait for task to reach terminal state.

        Raises:
            TaskFailedError: If task fails
            TimeoutError: If operation times out
        """
        start_time = time.time()

        while True:
            task = self.get(task_id)

            if task.is_terminal:
                if task.is_failed:
                    raise TaskFailedError(
                        task_id=task.id,
                        status=task.status.value,
                        message=task.message,
                        errors=task.errors,
                    )
                return task

            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Task {task_id} timed out after {timeout}s (status: {task.status})"
                )

            logger.debug(
                f"Task {task_id}: {task.status} ({task.progress}%), elapsed: {elapsed:.0f}s"
            )
            time.sleep(poll_interval)

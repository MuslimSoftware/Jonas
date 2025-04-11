from typing import Optional, Dict, Any
from beanie import PydanticObjectId
from datetime import datetime, timezone

from ..models import Task
from ..schemas import TaskStatus

class TaskRepository:
    """Handles database operations for Task models."""

    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        """Creates and returns a new Task document."""
        # Assuming task_data is already validated or comes from a trusted source
        # like the initial ChatWebSocketManager context.
        # Ensure core fields like chat_id, user_id, input_source_type, input_data are present.
        new_task = Task(**task_data)
        await new_task.create()
        return new_task

    async def get_task_by_id(self, task_id: PydanticObjectId) -> Optional[Task]:
        """Finds a task by its ID."""
        return await Task.get(task_id)

    async def update_task(self, task: Task, update_data: Dict[str, Any]) -> Task:
        """Updates a task document with the provided data, ensuring updated_at is set."""
        task.updated_at = datetime.now(timezone.utc)
        await task.update({"$set": update_data}) # Use $set for partial updates
        # Beanie's .update doesn't modify the instance in-place, so we need to refetch
        # or manually update the instance fields if needed immediately.
        # For simplicity, we just return the original instance, assuming the caller
        # knows the update happened or will refetch if necessary.
        return task

    async def save_task(self, task: Task) -> Task:
         """Saves the entire task document, ensuring updated_at is set."""
         task.updated_at = datetime.now(timezone.utc)
         await task.save()
         return task

    # Example helper specifically for status updates, which will be common
    async def update_task_status(
        self,
        task: Task,
        new_status: TaskStatus,
        error_details: Optional[str] = None
    ) -> Task:
        """Updates the task's status and optionally error details."""
        update_payload = {"status": new_status}
        if error_details is not None:
            update_payload["error_details"] = error_details
        elif new_status != TaskStatus.FAILED:
             # Clear error details if moving to a non-failed state
             update_payload["error_details"] = None
        else:
            # Ensure error_details field is included in update even if None (to clear it)
            update_payload["error_details"] = None 

        # Update the instance first
        task.status = new_status
        task.error_details = update_payload["error_details"]
        task.updated_at = datetime.now(timezone.utc)
        
        # Persist the changes using save (more reliable for instance state)
        await task.save() 
        return task 
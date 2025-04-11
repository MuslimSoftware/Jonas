from typing import TYPE_CHECKING, Optional
import asyncio
import traceback
from beanie import Document, PydanticObjectId

from ..models import Task
from ..schemas import TaskStatus, TaskData
from ..repositories import TaskRepository

if TYPE_CHECKING:
    # Use ConnectionRepository from chat feature for now
    # TODO: Refactor WebSocket broadcasting to a dedicated service
    from app.features.chat.services import WebSocketService

class TaskService: # Renamed from AgentOrchestrator
    """Service layer for managing and executing agent tasks."""

    def __init__(
        self,
        task_repository: TaskRepository,
        websocket_service: "WebSocketService"
        # TODO: Inject other necessary modules/services (Parser, DB Connector, etc.)
    ):
        self.task_repository = task_repository
        self.websocket_service = websocket_service # Store WebSocketService
        # TODO: Initialize other injected services

    async def _update_task_status(
        self,
        task: Task,
        new_status: TaskStatus,
        error: Optional[str] = None
    ) -> Task:
        """Updates task status in DB and broadcasts the change via WebSocketService."""
        updated_task = await self.task_repository.update_task_status(
            task=task,
            new_status=new_status,
            error_details=error
        )
        # Use WebSocketService to broadcast
        task_data_dict = TaskData.model_validate(updated_task).model_dump(by_alias=True)
        await self.websocket_service.broadcast_to_chat(
            chat_id=str(updated_task.chat_id),
            message_type="TASK_UPDATE",
            payload=task_data_dict
        )
        return updated_task

    # --- Workflow Phase Methods --- 
    # (_run_phase_gathering_context, _run_phase_planning, etc.)
    # ... methods remain the same ...
    async def _run_phase_gathering_context(self, task: Task) -> bool:
        """Placeholder for Phase 1: Context Gathering."""
        print(f"TaskService: Starting Phase 1 (Gathering Context) for task {task.id}...")
        task = await self._update_task_status(task, TaskStatus.GATHERING_CONTEXT)
        await asyncio.sleep(5) # Simulate work
        task.gathered_context = {"input": str(task.input_data), "mock_db_data": "some booking info"}
        await self.task_repository.save_task(task)
        print(f"TaskService: Finished Phase 1 for task {task.id}.")
        return True

    async def _run_phase_planning(self, task: Task) -> bool:
        """Placeholder for Phase 1b: Planning."""
        print(f"TaskService: Starting Phase 1b (Planning) for task {task.id}...")
        task = await self._update_task_status(task, TaskStatus.PLANNING)
        await asyncio.sleep(3)
        task.plan = "1. Find button component.\n2. Add mobile styles.\n3. Verify alignment."
        await self.task_repository.save_task(task)
        print(f"TaskService: Finished Phase 1b for task {task.id}.")
        return True

    async def _run_phase_implementing(self, task: Task) -> bool:
        """Placeholder for Phase 2: Implementation."""
        print(f"TaskService: Starting Phase 2 (Implementing) for task {task.id}...")
        task = await self._update_task_status(task, TaskStatus.IMPLEMENTING)
        await asyncio.sleep(5)
        print(f"TaskService: Finished Phase 2 for task {task.id}.")
        return True

    async def _run_phase_testing(self, task: Task) -> bool:
         """Placeholder for Phase 3: Testing."""
         print(f"TaskService: Starting Phase 3 (Testing) for task {task.id}...")
         task = await self._update_task_status(task, TaskStatus.TESTING)
         await asyncio.sleep(4)
         task.results = {"test_output": "All tests passed!", "status": "SUCCESS"}
         await self.task_repository.save_task(task)
         print(f"TaskService: Finished Phase 3 for task {task.id}.")
         return True

    async def _run_phase_creating_branch(self, task: Task) -> bool:
        """Placeholder for Phase 3b: Creating Git Branch."""
        print(f"TaskService: Starting Phase 3b (Creating Branch) for task {task.id}...")
        task = await self._update_task_status(task, TaskStatus.CREATING_BRANCH)
        await asyncio.sleep(2)
        branch_name = f"feature/jonas-{task.id}"
        if task.results:
             task.results["branch_name"] = branch_name
        else:
             task.results = {"branch_name": branch_name}
        await self.task_repository.save_task(task)
        print(f"TaskService: Finished Phase 3b for task {task.id}. Branch: {branch_name}")
        return True
    # --- End Workflow Phase Methods ---

    async def _execute_task_workflow(self, task_id: PydanticObjectId):
        """Runs the defined workflow phases for a given task ID."""
        task = await self.task_repository.get_task_by_id(task_id)
        # ... logic remains the same ...
        if not task:
            print(f"TaskService: Error - Task {task_id} not found for execution.")
            return
        if task.status not in [TaskStatus.PENDING, TaskStatus.FAILED]:
            print(f"TaskService: Task {task_id} already processing/completed (status: {task.status}). Skipping.")
            return
        try:
            print(f"TaskService: Starting workflow execution for task {task.id}")
            if not await self._run_phase_gathering_context(task): return
            if not await self._run_phase_planning(task): return
            if not await self._run_phase_implementing(task): return
            if not await self._run_phase_testing(task): return
            task = await self.task_repository.get_task_by_id(task.id)
            if not task: return
            if task.status != TaskStatus.FAILED and task.results and task.results.get("status") == "SUCCESS":
                if not await self._run_phase_creating_branch(task): return
            task = await self.task_repository.get_task_by_id(task.id)
            if not task: return
            if task.status != TaskStatus.FAILED:
                await self._update_task_status(task, TaskStatus.COMPLETED)
                print(f"TaskService: Task {task.id} completed successfully.")
        except Exception as e:
            print(f"TaskService: Unhandled exception during task {task_id} execution: {e}")
            error_str = traceback.format_exc()
            task = await self.task_repository.get_task_by_id(task_id)
            if task:
                await self._update_task_status(task, TaskStatus.FAILED, error=f"Unhandled exception: {error_str}")
            else:
                 print(f"TaskService: Error - Task {task_id} not found recording exception.")

    def start_task_execution(self, task_id: PydanticObjectId):
        """Public method to initiate the asynchronous execution of a task workflow."""
        # Renamed from start_task to be clearer
        print(f"TaskService: Received request to start execution for task {task_id}.")
        asyncio.create_task(self._execute_task_workflow(task_id))
        print(f"TaskService: Background execution scheduled for task {task_id}.") 
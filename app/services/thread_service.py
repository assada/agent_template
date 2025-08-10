from app.models import Thread
from app.repositories import ThreadRepository


class ThreadService:
    def __init__(self, thread_repository: ThreadRepository) -> None:
        self._repository: ThreadRepository = thread_repository

    def get_thread(self, thread_id: str) -> Thread:
        thread = self._repository.get_thread_by_id(thread_id)
        return thread
    
    async def create_thread(self, thread: Thread) -> Thread:
        return await self._repository.create_thread(thread)
    
    async def update_thread(self, thread: Thread) -> Thread:
        return await self._repository.update_thread(thread)

    def list_threads(self, user_id: str) -> list[Thread]:
        return self._repository.list_threads_by_user(user_id)

    def delete_thread(self, thread: Thread) -> None:
        return self._repository.delete_thread(thread)
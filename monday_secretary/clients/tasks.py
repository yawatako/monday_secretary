import os
from datetime import datetime, date
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .base import BaseClient, DEFAULT_RETRY


class TasksClient(BaseClient):
    """Minimal wrapper for Google Tasks API."""

    def __init__(self):
        self.creds = Credentials(
            None,
            refresh_token=os.getenv("GOOGLE_TASKS_REFRESH_TOKEN"),
            client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            token_uri="https://oauth2.googleapis.com/token",
        )
        self.service = build("tasks", "v1", credentials=self.creds)
        self.tasklist = os.getenv("GOOGLE_TASKS_LIST_ID", "@default")

    # ---- Core API ----
    @DEFAULT_RETRY
    async def list_tasks(self, show_completed: bool = False) -> list[dict]:
        def _call():
            return (
                self.service.tasks()
                .list(tasklist=self.tasklist, showCompleted=show_completed)
                .execute()
            )

        res = await self._to_thread(_call)
        return res.get("items", [])

    @DEFAULT_RETRY
    async def add_task(
        self,
        title: str,
        tags: list[str] | None = None,
        due: date | datetime | None = None,
    ) -> dict:
        body: dict = {"title": title}
        if tags:
            body["notes"] = " ".join(f"#{t}" for t in tags)
        if due:
            iso = due.isoformat() if isinstance(due, (datetime, date)) else str(due)
            body["due"] = iso if "T" in iso else iso + "T00:00:00Z"

        def _call():
            return (
                self.service.tasks()
                .insert(tasklist=self.tasklist, body=body)
                .execute()
            )

        return await self._to_thread(_call)

    @DEFAULT_RETRY
    async def complete_task(self, task_id: str) -> dict:
        def _call():
            return (
                self.service.tasks()
                .patch(tasklist=self.tasklist, task=task_id, body={"status": "completed"})
                .execute()
            )

        return await self._to_thread(_call)

    # ---- Helper ----
    async def find_task_by_title(self, title: str) -> dict | None:
        tasks = await self.list_tasks(show_completed=False)
        for t in tasks:
            if t.get("title") == title:
                return t
        return None

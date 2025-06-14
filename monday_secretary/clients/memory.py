import os
import asyncio
from notion_client import Client
from tenacity import retry, wait_fixed, stop_after_attempt


class MemoryClient:
    """Interact with Notion database."""

    def __init__(self):
        self.client = Client(auth=os.getenv("NOTION_TOKEN"))
        self.db_id = os.getenv("NOTION_DB_ID")

    async def _to_thread(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def create_record(self, **payload) -> dict:
        if "parent" not in payload:
            payload["parent"] = {"database_id": self.db_id}
        return await self._to_thread(self.client.pages.create, **payload)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def search(self, query: str, top_k: int = 5) -> list:
        def _call():
            return self.client.search(query=query, page_size=top_k)

        result = await self._to_thread(_call)
        return result.get("results", [])

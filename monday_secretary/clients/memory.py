import os
from datetime import datetime
from typing import Any, Dict

from notion_client import Client

from .base import BaseClient, DEFAULT_RETRY


class MemoryClient(BaseClient):
    """Interact with Notion database."""

    def __init__(self):
        self.client = Client(auth=os.getenv("NOTION_TOKEN"))
        self.db_id = os.getenv("NOTION_DB_ID")

        # DB のカラム名を列挙しておくと安全
        self.valid_props: set[str] = {
            "Title", "Summary", "Category",
            "Emotion", "Reason", "Timestamp"
        }


    # ---------- 内部ヘルパ ----------
    def _build_properties(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Notion に渡す properties を dict で構築"""
        props: Dict[str, Any] = {}

        # ヘルパで冗長な if 文を減らす
        def add(name: str, value: Dict[str, Any]):
            if name in self.valid_props:
                props[name] = value

        add("Title", {
            "title": [{"text": {"content": payload["title"]}}]
        })
        add("Summary", {
            "rich_text": [{"text": {"content": payload["summary"]}}]
        })
        add("Category", {"select": {"name": payload["category"]}})
        add("Emotion",  {"select": {"name": payload["emotion"]}})
        add("Reason", {
            "rich_text": [{"text": {"content": payload["reason"]}}]
        })
        add("Timestamp", {
            "date": {
                "start": (
                    payload.get("timestamp") or datetime.utcnow()
                ).isoformat()
            }
        })
        return props

    # ---------- Public API ----------
    @DEFAULT_RETRY
    async def create_record(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        page_body = {
            "parent": {"database_id": self.db_id},
            "properties": self._build_properties(payload)
        }
        return await self._to_thread(self.client.pages.create, **page_body)

    @DEFAULT_RETRY
    async def search(self, query: str, top_k: int = 5) -> list[Dict[str, Any]]:
        def _call():
            return self.client.search(query=query, page_size=top_k)

        result = await self._to_thread(_call)
        return result.get("results", [])

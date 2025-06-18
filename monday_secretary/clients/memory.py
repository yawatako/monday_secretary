import os
import asyncio
from datetime import datetime
from typing import Any, Dict

from notion_client import Client
from tenacity import retry, wait_fixed, stop_after_attempt


class MemoryClient:
    """Interact with Notion database."""

    def __init__(self):
        self.client = Client(auth=os.getenv("NOTION_TOKEN"))
        self.db_id = os.getenv("NOTION_DB_ID")

        # DB のカラム名を列挙しておくと安全
        self.valid_props: set[str] = {
            "タイトル", "要約", "カテゴリ",
            "感情", "理由", "タイムスタンプ"
        }

    # ---------- 共通ユーティリティ ----------
    async def _to_thread(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    # ---------- 内部ヘルパ ----------
    def _build_properties(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Notion に渡す properties を dict で構築"""
        props: Dict[str, Any] = {}

        # ヘルパで冗長な if 文を減らす
        def add(name: str, value: Dict[str, Any]):
            if name in self.valid_props:
                props[name] = value

        add("タイトル", {
            "title": [{"text": {"content": payload["title"]}}]
        })
        add("要約", {
            "rich_text": [{"text": {"content": payload["summary"]}}]
        })
        if payload.get("category"):
            add("カテゴリ", {"select": {"name": payload["category"]}})
        if payload.get("emotion"):
            add("感情",  {"select": {"name": payload["emotion"]}})
        if payload.get("reason"):
            add("理由", {
                "rich_text": [{"text": {"content": payload["reason"]}}]
            })
        add("タイムスタンプ", {
            "date": {
                "start": (
                    payload.get("timestamp") or datetime.utcnow()
                ).isoformat()
            }
        })
        return props

    # ---------- Public API ----------
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def create_record(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        page_body = {
            "parent": {"database_id": self.db_id},
            "properties": self._build_properties(payload)
        }
        return await self._to_thread(self.client.pages.create, **page_body)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def search(self, query: str, top_k: int = 5) -> list[Dict[str, Any]]:
        def _call():
            return self.client.search(query=query, page_size=top_k)

        result = await self._to_thread(_call)
        return result.get("results", [])

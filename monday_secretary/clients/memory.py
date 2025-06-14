# monday_secretary/clients/memory.py
import os
import asyncio
from datetime import datetime
from typing import Dict, Any

from notion_client import Client
from tenacity import retry, wait_fixed, stop_after_attempt


class MemoryClient:
    """Interact with Notion database (create / search)."""

    def __init__(self) -> None:
        self.client = Client(auth=os.getenv("NOTION_TOKEN"))
        self.db_id: str = os.getenv("NOTION_DB_ID", "")

    # ---------- ユーティリティ ----------
    async def _to_thread(self, func, *args, **kwargs):
        """同期関数をスレッドで非同期実行"""
        return await asyncio.to_thread(func, *args, **kwargs)

    # ---------- 追加：ペイロード変換 ----------
    @staticmethod
    def _build_properties(payload: Dict[str, Any]) -> Dict[str, Any]:
        """MemoryRequest(dict) → Notion properties"""
        props = {
            "Title": {
                "title": [{"text": {"content": payload["title"]}}],
            },
            "Summary": {
                "rich_text": [{"text": {"content": payload["summary"]}}],
            },
            "Category": {
                "select": {"name": payload["category"]},
            },
            "Emotion": {
                "select": {"name": payload["emotion"]},
            },
            "Reason": {
                "rich_text": [{"text": {"content": payload["reason"]}}],
            },
            "Timestamp": {
                "date": {
                    "start": (
                        payload.get("timestamp") or datetime.utcnow()
                    ).isoformat()
                },
            },
        }

        # 任意フィールド detail
        if payload.get("detail"):
            props["Detail"] = {
                "rich_text": [{"text": {"content": payload["detail"]}}],
            }
        return props

    # ---------- ページ作成 ----------
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def create_record(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        MemoryRequest → Notion ページを作成して結果(JSON) を返す
        """
        try:
            page_body = {
                "parent": {"database_id": self.db_id},
                "properties": self._build_properties(payload),
            }
            return await self._to_thread(self.client.pages.create, **page_body)

        except Exception as e:  # 失敗時はログを残して再送出
            import logging, traceback

            logging.error(
                "Notion create_record failed: %s\n%s",
                e,
                traceback.format_exc(),
            )
            raise

    # ---------- 検索 ----------
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def search(self, query: str, top_k: int = 5) -> list:
        """全文検索 (title/テキスト) して上位 top_k 件の結果を返す"""
        def _call():
            return self.client.search(
                query=query,
                page_size=top_k,
                sort={"direction": "descending", "timestamp": "last_edited_time"},
            )

        result = await self._to_thread(_call)
        return result.get("results", [])

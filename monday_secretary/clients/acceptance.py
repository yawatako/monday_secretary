import os
import asyncio
from datetime import date, datetime

import gspread
from tenacity import retry, wait_fixed, stop_after_attempt

class AcceptanceClient:
    """「自己受容」タブの読み取りクライアント"""

    def __init__(self) -> None:
        sa_path   = os.getenv("GOOGLE_SA_JSON_PATH")
        sheet_url = os.getenv("SHEET_URL")
        self.gc    = gspread.service_account(filename=sa_path)
        self.sheet = self.gc.open_by_url(sheet_url).worksheet("自己受容")

    # ---------- 内部 util ----------
    async def _to_thread(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    @staticmethod
    def _to_date(s: str) -> date:
        """'2025/06/18' or '2025-06-18' → datetime.date"""
        return datetime.fromisoformat(s.replace("/", "-")).date()

    # ---------- 取得メソッド ----------
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def latest(self) -> dict:
        rows = await self._to_thread(self.sheet.get_all_records)
        return rows[-1] if rows else {}

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def period(self, start: date | str, end: date | str) -> list[dict]:
        start_d = start if isinstance(start, date) else self._to_date(start)
        end_d   = end   if isinstance(end,   date) else self._to_date(end)

        rows = await self._to_thread(self.sheet.get_all_records)
        return [
            r for r in rows
            if start_d <= self._to_date(r["タイムスタンプ"]) <= end_d
        ]

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def today(self) -> dict | None:
        today = date.today()
        rows  = await self._to_thread(self.sheet.get_all_records)
        for r in reversed(rows):              # 新しい方から探すと速い
            if self._to_date(r["タイムスタンプ"]) == today:
                return r
        return None

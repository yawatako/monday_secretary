import os
import asyncio
import gspread
from tenacity import retry, wait_fixed, stop_after_attempt
from datetime import date, datetime

class AcceptanceClient:
    """「自己受容」タブの読み取りクライアント"""

    def __init__(self):
        sa_path   = os.getenv("GOOGLE_SA_JSON_PATH")
        sheet_url = os.getenv("SHEET_URL")
        self.gc     = gspread.service_account(filename=sa_path)
        self.sheet  = self.gc.open_by_url(sheet_url).worksheet("自己受容")

    # ↓↓↓ これが無かったので追加 ↓↓↓
    async def _to_thread(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    # ↑↑↑ ここまで ↑↑↑

    # ─── 共通ヘルパ：文字列→date ─────────────────────
    @staticmethod
    def _to_date(s: str) -> date:
        """ '2025/06/18' or '2025-06-18' → date 型 """
        return datetime.fromisoformat(s.replace("/", "-")).date()

    # ─── 最新１件 ────────────────────────────────
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def latest(self) -> dict:
        rows = await self._to_thread(self.sheet.get_all_records)
        return rows[-1] if rows else {}

    # ─── 期間指定（start〜end を含む）────────────────
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def period(self, start: date | str, end: date | str) -> list[dict]:
        start_d = start if isinstance(start, date) else self._to_date(start)
        end_d   = end   if isinstance(end,   date) else self._to_date(end)

        rows = await self._to_thread(self.sheet.get_all_records)
        return [r for r in rows
                if start_d <= self._to_date(r["タイムスタンプ"]) <= end_d]

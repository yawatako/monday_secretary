import os, asyncio, gspread
from tenacity import retry, wait_fixed, stop_after_attempt

class AcceptanceClient:
    def __init__(self):
        sa_path   = os.getenv("GOOGLE_SA_JSON_PATH")
        sheet_url = os.getenv("SHEET_URL")
        self.gc    = gspread.service_account(filename=sa_path)
        # 「自己受容」タブを明示
        self.sheet = self.gc.open_by_url(sheet_url).worksheet("自己受容")

    async def _rows(self) -> list[dict]:
        """全行をスレッドで取得して返す"""
        return await asyncio.to_thread(self.sheet.get_all_records)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def latest(self) -> dict:
        rows = await self._rows()
        return rows[-1] if rows else {}

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def period(self, start: str, end: str) -> list[dict]:
        rows = await self._rows()
        return [r for r in rows if start <= r["タイムスタンプ"] <= end]

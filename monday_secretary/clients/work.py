import os, asyncio, gspread
from tenacity import retry, wait_fixed, stop_after_attempt


class WorkClient:
    """業務メモ（《業務記録》タブ）を取得"""

    def __init__(self):
        sa_path   = os.getenv("GOOGLE_SA_JSON_PATH")
        sheet_url = os.getenv("SHEET_URL")                 # 体調と同じファイル
        self.gc      = gspread.service_account(filename=sa_path)
        self.sheet   = self.gc.open_by_url(sheet_url).worksheet("業務記録")  # ← 変更!!

    async def _to_thread(self, f, *a, **kw):
        return await asyncio.to_thread(f, *a, **kw)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def latest(self) -> dict:
        rows = await self._to_thread(self.sheet.get_all_records)
        return rows[-1] if rows else {}

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def period(self, start: str, end: str) -> list[dict]:
        rows = await self._to_thread(self.sheet.get_all_records)
        return [r for r in rows if start <= r.get("タイムスタンプ", "") <= end]

    async def today(self) -> dict | None:
    today_d = date.today()
    rows = await self._to_thread(self.sheet.get_all_records)
    for r in reversed(rows):
        if self._to_date(r["タイムスタンプ"]) == today_d:
            return r
    return None

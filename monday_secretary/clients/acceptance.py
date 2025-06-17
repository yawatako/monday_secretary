import os, asyncio, gspread
from tenacity import retry, wait_fixed, stop_after_attempt
from ..models import AcceptanceItem

class AcceptanceClient:
    def __init__(self):
        sa_path   = os.getenv("GOOGLE_SA_JSON_PATH")
        sheet_url = os.getenv("SHEET_URL")
        self.gc     = gspread.service_account(filename=sa_path)
        self.sheet  = self.gc.open_by_url(sheet_url).worksheet("自己受容")

    async def _io(self, fn, *a, **kw):
        return await asyncio.to_thread(fn, *a, **kw)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def latest(self) -> AcceptanceItem:
        recs = await self._io(self.sheet.get_all_records)
        return AcceptanceItem(**recs[-1]) if recs else None

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def period(self, start: str, end: str):
        recs = await self._io(self.sheet.get_all_records)
        return [AcceptanceItem(**r) for r in recs if start <= r["タイムスタンプ"] <= end]

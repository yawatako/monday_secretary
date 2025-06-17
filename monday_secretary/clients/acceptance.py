import os, asyncio, gspread
from tenacity import retry, wait_fixed, stop_after_attempt
from ..models import AcceptanceItem

class AcceptanceClient:
    def __init__(self):
        sa_path   = os.getenv("GOOGLE_SA_JSON_PATH")
        sheet_url = os.getenv("SHEET_URL")
        self.gc   = gspread.service_account(filename=sa_path)
        self.sheet = self.gc.open_by_url(sheet_url).worksheet("自己受容")

    async def _io(self, fn, *a, **kw):
        return await asyncio.to_thread(fn, *a, **kw)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def latest(self):
        return await asyncio.to_thread(self.sheet.get_all_records)[-1]

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def period(self, start, end):
        rows = await asyncio.to_thread(self.sheet.get_all_records)
        return [r for r in rows if start <= r["タイムスタンプ"] <= end]

import os
import asyncio
import gspread
from tenacity import retry, wait_fixed, stop_after_attempt


class HealthClient:
    """Read health logs from Google Sheets."""

    def __init__(self):
        sa_path = os.getenv("GOOGLE_SA_JSON_PATH")
        sheet_url = os.getenv("SHEET_URL")
        self.gc = gspread.service_account(filename=sa_path)
        self.sheet = self.gc.open_by_url(sheet_url).sheet1

    async def _to_thread(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def latest(self) -> dict:
        records = await self._to_thread(self.sheet.get_all_records)
        return records[-1] if records else {}

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def compare(self) -> dict:
        records = await self._to_thread(self.sheet.get_all_records)
        if len(records) < 2:
            return {}
        latest, prev = records[-1], records[-2]
        diff = {}
        for k, v in latest.items():
            pv = prev.get(k)
            if isinstance(v, (int, float)) and isinstance(pv, (int, float)):
                diff[k] = v - pv
        return diff

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def period(self, start: str, end: str) -> list:
        records = await self._to_thread(self.sheet.get_all_records)
        return [r for r in records if start <= r.get("Date", "") <= end]

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def daily_summary(self, date: str) -> dict:
        records = await self._to_thread(self.sheet.get_all_records)
        for r in records:
            if r.get("Date") == date:
                return r
        return {}

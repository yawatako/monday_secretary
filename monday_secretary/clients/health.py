import os
from datetime import date, datetime
import gspread

from .base import BaseClient, DEFAULT_RETRY


class HealthClient(BaseClient):
    """Read health logs from Google Sheets."""

    def __init__(self):
        sa_path = os.getenv("GOOGLE_SA_JSON_PATH")
        sheet_url = os.getenv("SHEET_URL")
        self.gc = gspread.service_account(filename=sa_path)
        self.sheet = self.gc.open_by_url(sheet_url).sheet1


    @staticmethod
    def _to_date(s: str) -> date:
        """'YYYY/MM/DD' or 'YYYY-MM-DD' or with time -> date"""
        part = s.replace("/", "-").split()[0]
        return datetime.fromisoformat(part).date()

    @DEFAULT_RETRY
    async def latest(self) -> dict:
        records = await self._to_thread(self.sheet.get_all_records)
        return records[-1] if records else {}

    @DEFAULT_RETRY
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

    @DEFAULT_RETRY
    async def period(self, start: date | str, end: date | str) -> list[dict]:
        start_d = start if isinstance(start, date) else self._to_date(start)
        end_d = end if isinstance(end, date) else self._to_date(end)

        records = await self._to_thread(self.sheet.get_all_records)
        return [
            r for r in records if start_d <= self._to_date(r["タイムスタンプ"]) <= end_d
        ]

    @DEFAULT_RETRY
    async def daily_summary(self, date: str) -> dict:
        records = await self._to_thread(self.sheet.get_all_records)
        for r in records:
            if r.get("Date") == date:
                return r
        return {}

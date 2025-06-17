import os
import asyncio
from datetime import date, datetime 


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
    async def period(
        self,
        start: date | str | None,
        end:   date | str | None
    ) -> list[dict]:

        # --- デフォルト値を今日にする -------------------------
        today = date.today()
        start_d = (
            today if start is None
            else start if isinstance(start, date)
            else self._to_date(start)
        )
        end_d = (
            today if end is None
            else end if isinstance(end, date)
            else self._to_date(end)
        )

        rows = await self._to_thread(self.sheet.get_all_records)
        return [
            r for r in rows
            if start_d <= self._to_date(r["タイムスタンプ"]) <= end_d
        ]

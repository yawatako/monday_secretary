import os
import asyncio
import gspread
from tenacity import retry, wait_fixed, stop_after_attempt

class AcceptanceClient:
    """Google Sheets の『自己受容』タブを読むだけ。"""
    COL_DATE  = "タイムスタンプ"
    COL_FEEL_NOW   = "今の気持ち"
    COL_STRONGEST  = "一番印象的だった感情"
    COL_THOUGHT    = "今日浮かんだ思考の断片"
    COL_MESSAGE    = "今日の自分にかけたい言葉"
    COL_ACCEPTED   = "今日、『自分を受け入れられた』瞬間はある？"
    COL_MUST_WRITE = "書き残しておきたいこと"
    
    def __init__(self):
        sa_path = os.getenv("GOOGLE_SA_JSON_PATH")
        sheet_url = os.getenv("SHEET_URL")
        self.gc = gspread.service_account(filename=sa_path)
        self.sheet = self.gc.open_by_url(sheet_url).worksheet("自己受容")

    async def period(self, start: str, end: str) -> list:
        rows = await self._to_thread(self.sheet.get_all_records)
        return [r for r in rows if start <= r.get(self.COL_DATE, "") <= end]

    # ---- 最新 1 行
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def latest(self) -> dict:
        rows = await self._to_thread(self.sheet.get_all_records)
        return rows[-1] if rows else {}

    # ---- 期間取得
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def period(self, start: str, end: str) -> list:
        rows = await self._to_thread(self.sheet.get_all_records)
        return [r for r in rows if start <= r.get("日付", "") <= end]

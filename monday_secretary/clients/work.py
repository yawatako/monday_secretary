from __future__ import annotations

import os
import asyncio
from datetime import date
from typing import List, Dict

import gspread
from tenacity import retry, wait_fixed, stop_after_attempt

# 共通ヘルパ：文字列 → date 変換
from monday_secretary.utils.date import to_date


class WorkClient:
    """Google シートの〈業務記録〉タブを読む軽量クライアント"""

    def __init__(self) -> None:
        sa_path = os.getenv("GOOGLE_SA_JSON_PATH")
        sheet_url = os.getenv("SHEET_URL")

        self.gc = gspread.service_account(filename=sa_path)
        self.sheet = self.gc.open_by_url(sheet_url).worksheet("業務記録")

    # ───────────── 内部ユーティリティ ──────────────
    async def _to_thread(self, func, *args, **kwargs):
        """同期 gspread 呼び出しをスレッドに逃がして async 化"""
        return await asyncio.to_thread(func, *args, **kwargs)

    # ───────────── API: 最新 1 行 ───────────────
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def latest(self) -> Dict:
        rows = await self._to_thread(self.sheet.get_all_records)
        return rows[-1] if rows else {}

    # ───────────── API: 期間取得 ───────────────
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def period(
        self,
        start: date | str | None,
        end: date | str | None,
    ) -> List[Dict]:
        """
        `start`〜`end`(含む) の行を返す。
        引数が None の場合はシート全体を返す。
        """
        rows = await self._to_thread(self.sheet.get_all_records)
        if start is None and end is None:
            return rows  # フルダンプ

        start_d = start if isinstance(start, date) else to_date(start)
        end_d = end if isinstance(end, date) else to_date(end)

        return [
            r
            for r in rows
            if start_d <= to_date(r["タイムスタンプ"]) <= end_d
        ]
        

import os
import sys
import asyncio
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from monday_secretary.clients.health import HealthClient

class DummySheet:
    def get_all_records(self):
        return [
            {"タイムスタンプ": "2025-06-10", "睡眠時間": 6},
            {"タイムスタンプ": "2025-06-11", "睡眠時間": 7},
            {"タイムスタンプ": "2025-06-12", "睡眠時間": 5},
        ]

@pytest.mark.asyncio
async def test_period_slice(monkeypatch):
    hc = object.__new__(HealthClient)
    hc.sheet = DummySheet()
    async def dummy_thread(func, *a, **kw):
        return func(*a, **kw)
    monkeypatch.setattr(hc, "_to_thread", dummy_thread)
    result = await HealthClient.period(hc, "2025-06-11", "2025-06-12")
    assert len(result) == 2

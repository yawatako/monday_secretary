import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from monday_secretary.main_handler import handle_message

class DummyBrake:
    def __init__(self, level: int = 1):
        self.level = level
    def dict(self):
        return {"level": self.level}

@pytest.mark.asyncio
async def test_morning_trigger(monkeypatch):
    class DummyHealth:
        async def latest(self):
            return {"状態": "良好"}

    class DummyCal:
        async def get_events(self, start, end):
            return [{"summary": "会議", "start": {"dateTime": "2025-06-18T10:00:00"}}]

    class DummyWork:
        async def latest(self):
            raise AssertionError("WorkClient should not be used in morning trigger")

    monkeypatch.setattr("monday_secretary.main_handler.HealthClient", DummyHealth)
    monkeypatch.setattr("monday_secretary.main_handler.CalendarClient", DummyCal)
    monkeypatch.setattr("monday_secretary.main_handler.WorkClient", DummyWork)
    monkeypatch.setattr("monday_secretary.main_handler.AcceptanceClient", lambda: None)
    monkeypatch.setattr("monday_secretary.main_handler.BrakeChecker.check", lambda self, h, w={}: DummyBrake(1))
    from monday_secretary import main_handler
    main_handler.MORNING_LOCKS.clear()
    main_handler.LAST_MORNING.clear()

    reply = await handle_message("おはよう！")
    assert "**Monday**" in reply
    assert "良好" in reply
    assert "会議" in reply
    assert "業務" not in reply

@pytest.mark.asyncio
async def test_normal_flow(monkeypatch):
    class DummyHealth:
        async def latest(self):
            return {"状態": "普通"}

    class DummyWork:
        async def latest(self):
            return {}

    monkeypatch.setattr("monday_secretary.main_handler.HealthClient", DummyHealth)
    monkeypatch.setattr("monday_secretary.main_handler.WorkClient", DummyWork)
    monkeypatch.setattr("monday_secretary.main_handler.BrakeChecker.check", lambda self, h, w={}: DummyBrake(1))
    from monday_secretary import main_handler
    main_handler.MORNING_LOCKS.clear()
    main_handler.LAST_MORNING.clear()
    monkeypatch.setattr("monday_secretary.main_handler.AcceptanceClient", lambda: None)

    reply = await handle_message("今日の体調教えて")
    assert "<CONTEXT>" in reply
    assert "普通" in reply


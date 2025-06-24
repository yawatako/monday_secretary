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
        async def get_events(self, start, end, tz=None):
            return [
                {"summary": "会議", "start": {"dateTime": "2025-06-18T10:00:00"}},
                {"summary": "休暇", "start": {"date": "2025-06-18"}, "end": {"date": "2025-06-19"}},
            ]

    class DummyWork:
        async def latest(self):
            raise AssertionError("WorkClient should not be used in morning trigger")

    monkeypatch.setattr("monday_secretary.main_handler.HealthClient", DummyHealth)
    monkeypatch.setattr("monday_secretary.main_handler.CalendarClient", DummyCal)
    monkeypatch.setattr("monday_secretary.main_handler.WorkClient", DummyWork)
    monkeypatch.setattr("monday_secretary.main_handler.BrakeChecker.check", lambda self, h, w={}: DummyBrake(1))
    from monday_secretary import main_handler
    main_handler.MORNING_LOCKS.clear()
    main_handler.LAST_MORNING.clear()

    reply = await handle_message("おはよう！")
    assert "**Monday**" in reply
    assert "良好" in reply
    assert "会議" in reply
    assert "休暇" in reply
    assert "終日" in reply
    assert "業務" not in reply

@pytest.mark.asyncio
async def test_normal_flow(monkeypatch):
    class DummyHealth:
        async def latest(self):
            return {"状態": "普通"}

    class DummyWork:
        async def latest(self):
            return {}

    class DummyCal:
        async def get_events(self, start, end, tz=None):
            return []

    monkeypatch.setattr("monday_secretary.main_handler.HealthClient", DummyHealth)
    monkeypatch.setattr("monday_secretary.main_handler.WorkClient", DummyWork)
    monkeypatch.setattr("monday_secretary.main_handler.CalendarClient", DummyCal)
    monkeypatch.setattr("monday_secretary.main_handler.BrakeChecker.check", lambda self, h, w={}: DummyBrake(1))
    from monday_secretary import main_handler
    main_handler.MORNING_LOCKS.clear()
    main_handler.LAST_MORNING.clear()

    reply = await handle_message("今日の体調教えて")
    assert "<CONTEXT>" in reply
    assert "普通" in reply


@pytest.mark.asyncio
async def test_weekend_trigger(monkeypatch):
    class DummyTasks:
        async def list_tasks(self):
            return [
                {"title": "T1", "notes": "#優先度/高", "due": "2025-06-19"},
                {"title": "T2", "notes": "#優先度/低", "due": "2025-06-20"},
                {"title": "T3", "notes": "#緊急度/高", "due": "2025-06-21"},
            ]

    class DummyCal:
        def __init__(self):
            self.calls = 0

        async def get_events(self, start, end, tz=None):
            self.calls += 1
            if self.calls == 1:
                return [
                    {"summary": "会議", "start": {"dateTime": "2025-06-18T10:00:00"}}
                ]
            return [
                {"summary": "来週会議", "start": {"dateTime": "2025-06-25T09:00:00"}}
            ]

    class DummyHealth:
        async def latest(self):
            return {}

    class DummyWork:
        async def latest(self):
            return {}

    monkeypatch.setattr("monday_secretary.main_handler.TasksClient", DummyTasks)
    monkeypatch.setattr("monday_secretary.main_handler.CalendarClient", DummyCal)
    monkeypatch.setattr("monday_secretary.main_handler.HealthClient", DummyHealth)
    monkeypatch.setattr("monday_secretary.main_handler.WorkClient", DummyWork)

    reply = await handle_message("週末整理して")
    assert "T1" in reply
    assert "T3" in reply
    assert "T2" not in reply
    assert "来週会議" in reply


from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime
from zoneinfo import ZoneInfo
from .base import BaseClient, DEFAULT_RETRY, SA_PATH, SCOPES_CALENDAR

class CalendarClient(BaseClient):
    """Access Google Calendar API."""

    def __init__(self):
        self.creds = service_account.Credentials.from_service_account_file(
            SA_PATH,
            scopes=SCOPES_CALENDAR,
        )
        self.service = build("calendar", "v3", credentials=self.creds)

    def _to_iso(self, dt_or_str: datetime | str, tz: str) -> str:
        """Convert datetime or string to ISO-8601 with timezone"""
        if isinstance(dt_or_str, datetime):
            if dt_or_str.tzinfo is None:
                dt_or_str = dt_or_str.replace(tzinfo=ZoneInfo(tz))
            return dt_or_str.isoformat()
        return dt_or_str

    @DEFAULT_RETRY
    async def get_events(self, time_min: datetime | str, time_max: datetime | str, tz: str = "Asia/Tokyo") -> list:
        def _call():
            params = {
                "calendarId": "primary",
                "timeMin": self._to_iso(time_min, tz),
                "timeMax": self._to_iso(time_max, tz),
                "singleEvents": True,
                "orderBy": "startTime",
                "timeZone": tz,
            }
            events = self.service.events().list(**params).execute()
            return events.get("items", [])

        return await self._to_thread(_call)

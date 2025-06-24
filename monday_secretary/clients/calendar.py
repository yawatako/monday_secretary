from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from os import getenv
from .base import BaseClient, DEFAULT_RETRY, SA_PATH, SCOPES_CALENDAR

DEFAULT_CAL_ID = getenv("CALENDAR_ID", "yawata.three.personalities@gmail.com")


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
    async def get_events(
        self,
        time_min: datetime | str | None = None,
        time_max: datetime | str | None = None,
        tz: str = "Asia/Tokyo",
        calendar_id: str | None = None,
    ) -> list:
        tzinfo = ZoneInfo(tz)
        if time_min is None or time_max is None:
            today = datetime.now(ZoneInfo(tz)).date()
            if time_min is None:
                time_min = datetime.combine(today, time.min, tzinfo)
            if time_max is None:
                time_max = datetime.combine(today, time.max, tzinfo)

        cal_id = calendar_id or DEFAULT_CAL_ID

        def _call():
            params = {
                "calendarId": cal_id,
                "timeMin": self._to_iso(time_min, tz),
                "timeMax": self._to_iso(time_max, tz),
                "singleEvents": True,
                "orderBy": "startTime",
                "timeZone": tz,
            }
            events = self.service.events().list(**params).execute()
            return events.get("items", [])
        
        return await self._to_thread(_call)

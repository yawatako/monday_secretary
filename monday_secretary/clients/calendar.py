import os
from googleapiclient.discovery import build
from google.oauth2 import service_account

from .base import (
    BaseClient,
    DEFAULT_RETRY,
    SA_PATH,
    SCOPES_CALENDAR,
)


class CalendarClient(BaseClient):
    """Access Google Calendar API."""

    async def get_events(
        self,
        time_min: str,
        time_max: str,
        tz: str = "Asia/Tokyo",
    ) -> list:
        def _call():
            params = {
                "calendarId": "primary",
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": True,
                "orderBy": "startTime",
                "timeZone": tz,        # ← ここでタイムゾーンをまとめて指定
            }
            events = self.service.events().list(**params).execute()
            return events.get("items", [])

        return await self._to_thread(_call)


    @DEFAULT_RETRY
    async def get_events(self, time_min: str, time_max: str, tz: str | None = None) -> list:
        def _call():
            params = {
                "calendarId": "primary",
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": True,
                "orderBy": "startTime",
            }
            if tz:
                params["timeZone"] = tz

            events = self.service.events().list(**params).execute()
            return events.get("items", [])

        return await self._to_thread(_call)

    @DEFAULT_RETRY
    async def insert_event(self, summary: str, start: str, end: str) -> dict:
        body = {
            "summary": summary,
            "start": {"dateTime": start},
            "end": {"dateTime": end},
        }

        def _call():
            return (
                self.service.events()
                .insert(calendarId="primary", body=body)
                .execute()
            )

        return await self._to_thread(_call)

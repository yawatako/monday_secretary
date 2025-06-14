import os
import asyncio
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from tenacity import retry, wait_fixed, stop_after_attempt


class CalendarClient:
    """Access Google Calendar API."""

    def __init__(self):
        self.creds = Credentials(
            None,
            refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            token_uri="https://oauth2.googleapis.com/token",
        )
        self.service = build("calendar", "v3", credentials=self.creds)

    async def _to_thread(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    async def get_events(self, time_min: str, time_max: str) -> list:
        def _call():
            events = (
                self.service.events()
                .list(calendarId="primary", timeMin=time_min, timeMax=time_max)
                .execute()
            )
            return events.get("items", [])

        return await self._to_thread(_call)

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
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

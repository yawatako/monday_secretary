import os
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as SACredentials
from googleapiclient.discovery import build

from .base import BaseClient, DEFAULT_RETRY


class CalendarClient(BaseClient):
    """Access Google Calendar API."""

    def __init__(self):
        sa_path = os.getenv("GOOGLE_CAL_SA_JSON_PATH")
        if sa_path:
            self.creds = SACredentials.from_service_account_file(
                sa_path, scopes=["https://www.googleapis.com/auth/calendar"]
            )
        else:
            self.creds = Credentials(
                None,
                refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
                token_uri="https://oauth2.googleapis.com/token",
            )
        self.service = build("calendar", "v3", credentials=self.creds)


    @DEFAULT_RETRY
    async def get_events(self, time_min: str, time_max: str) -> list:
        def _call():
            events = (
                self.service.events()
                .list(calendarId="primary", timeMin=time_min, timeMax=time_max)
                .execute()
            )
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

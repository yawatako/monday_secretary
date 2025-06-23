from googleapiclient.discovery import build
from google.oauth2 import service_account
from .base import BaseClient, DEFAULT_RETRY, SA_PATH, SCOPES_CALENDAR

class CalendarClient(BaseClient):
    """Access Google Calendar API."""

    def __init__(self):
        self.creds = service_account.Credentials.from_service_account_file(
            SA_PATH,
            scopes=SCOPES_CALENDAR,
        )
        self.service = build("calendar", "v3", credentials=self.creds)

    @DEFAULT_RETRY
    async def get_events(self, time_min: str, time_max: str, tz: str = "Asia/Tokyo") -> list:
        def _call():
            params = {
                "calendarId": "primary",
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": True,
                "orderBy": "startTime",
                "timeZone": tz,
            }
            events = self.service.events().list(**params).execute()
            return events.get("items", [])

        return await self._to_thread(_call)

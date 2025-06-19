import asyncio
import os
from google.oauth2 import service_account
from tenacity import retry, wait_fixed, stop_after_attempt

class BaseClient:
    """Provide shared async helpers for API clients."""

    async def _to_thread(self, func, *args, **kwargs):
        """Run blocking call in a thread."""
        return await asyncio.to_thread(func, *args, **kwargs)

DEFAULT_RETRY = retry(wait=wait_fixed(2), stop=stop_after_attempt(3))

# -- Google Service Account path & scopes -----------------------------------
SA_PATH = os.getenv("GOOGLE_SA_JSON_PATH")

SCOPES_SHEETS = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SCOPES_CALENDAR = ["https://www.googleapis.com/auth/calendar"]
SCOPES_ALL = SCOPES_SHEETS + SCOPES_CALENDAR


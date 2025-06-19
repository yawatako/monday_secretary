import asyncio
from tenacity import retry, wait_fixed, stop_after_attempt

class BaseClient:
    """Provide shared async helpers for API clients."""

    async def _to_thread(self, func, *args, **kwargs):
        """Run blocking call in a thread."""
        return await asyncio.to_thread(func, *args, **kwargs)

DEFAULT_RETRY = retry(wait=wait_fixed(2), stop=stop_after_attempt(3))


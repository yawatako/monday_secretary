import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from monday_secretary.clients import CalendarClient

async def main():
    jst = ZoneInfo("Asia/Tokyo")
    start = datetime.now(jst).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1, seconds=-1)

    client = CalendarClient()
    events = await client.get_events(start, end)
    for ev in events:
        print(ev.get("summary"))

if __name__ == "__main__":
    asyncio.run(main())

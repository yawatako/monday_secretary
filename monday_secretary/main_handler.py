import asyncio
import datetime
from dotenv import load_dotenv

from .clients import HealthClient, CalendarClient, MemoryClient
from .utils import BrakeChecker
from .prompts import template

load_dotenv()


async def handle_message(user_msg: str) -> str:
    health_client = HealthClient()
    calendar_client = CalendarClient()
    memory_client = MemoryClient()
    checker = BrakeChecker()

    context = {}

    # naive routing based on keywords
    health = {}
    if "health" in user_msg:
        health = await health_client.latest()
        context["health"] = health

    if "calendar" in user_msg:
        now = datetime.datetime.utcnow().isoformat() + "Z"
        events = await calendar_client.get_events(now, now)
        context["events"] = events

    if "remember" in user_msg:
        results = await memory_client.search(user_msg)
        context["memories"] = results

    brake = checker.check(health, {})
    context["brake"] = brake.dict()

    prompt = template.build_prompt(user_msg, context)
    return prompt


def main() -> None:
    import sys

    user_msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "health"
    output = asyncio.run(handle_message(user_msg))
    print(output)


if __name__ == "__main__":
    main()

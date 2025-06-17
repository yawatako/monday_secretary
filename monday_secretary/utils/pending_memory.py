import asyncio

PENDING: dict[str, str] = {}   # session_id -> summary

def store_pending(sid: str, summary: str):
    PENDING[sid] = summary
    asyncio.get_event_loop().call_later(60, PENDING.pop, sid, None)

def pop_pending(sid: str) -> str | None:
    return PENDING.pop(sid, None)

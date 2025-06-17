PENDING: dict[str, str] = {}   # session_id -> summary

def _store_pending(sid: str, summary: str):
    PENDING[sid] = summary
    # タイムアウトで自動削除
    asyncio.get_event_loop().call_later(60, PENDING.pop, sid, None)

def pop_pending(sid: str) -> str | None:
    return PENDING.pop(sid, None)

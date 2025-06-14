"""
FastAPI entrypoint for Render web service.
Exposes:
  GET  /healthcheck   – liveness probe
  POST /chat          – proxy to main_handler.handle_message
  POST /health        – 体調データ取得
  POST /calendar      – カレンダー操作
  POST /memory        – Notion に記憶保存
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from .main_handler import handle_message
from .models import HealthRequest, CalendarRequest, MemoryRequest
from .clients.health import HealthClient
from .clients.calendar import CalendarClient
from .clients.memory import MemoryClient

app = FastAPI(title="Monday Secretary API")


# ---------- Chat (既存) ----------
class ChatRequest(BaseModel):
    user_msg: str


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        reply: str = await handle_message(req.user_msg)
        return {"reply": reply}
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Health ----------
@app.post("/health")
async def health_api(req: HealthRequest):
    client = HealthClient()
    try:
        match req.mode:
            case "latest":
                data = await client.latest()
            case "compare":
                data = await client.compare()
            case "period":
                data = await client.period(
                    req.start_date, req.end_date
                )
            case "dailySummary":
                data = await client.daily_summary(
                    req.start_date or client.today
                )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# OpenAPI alias
@app.post("/functions/get_health_data", tags=["functions"])
async def get_health_data_alias(req: HealthRequest):
    """OpenAPI 用エイリアス"""
    return await health_api(req)


# ---------- Calendar ----------
@app.post("/calendar")
async def calendar_api(req: CalendarRequest):
    client = CalendarClient()
    try:
        match req.action:
            case "insert":
                data = await client.insert_event(
                    req.summary, req.start, req.end, req.calendar_id
                )
            case "get":
                data = await client.get_events(
                    req.start, req.end, req.calendar_id
                )
            case "update":
                data = await client.update_event(
                    req.event_id, req.summary, req.start, req.end
                )
            case "delete":
                data = await client.delete_event(req.event_id)
        return data or {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# OpenAPI alias
@app.post("/functions/calendar_event", tags=["functions"])
async def calendar_event_alias(req: CalendarRequest):
    return await calendar_api(req)

# ---------- Memory ----------
@app.post("/memory")
async def memory_api(req: MemoryRequest):
    client = MemoryClient()
    try:
        record_id: str = client.create_record(req.model_dump())
        return {"inserted": record_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Healthcheck (既存) ----------
@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok", "version": "0.1.0"}

# OpenAPI alias
@app.post("/functions/create_memory", tags=["functions"])
async def create_memory_alias(req: MemoryRequest):
    return await memory_api(req)

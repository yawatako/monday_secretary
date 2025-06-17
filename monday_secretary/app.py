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
from .models import (
    HealthRequest, CalendarRequest, MemoryRequest,
    MemorySearchRequest,
from .clients.health import HealthClient
from .clients.work import WorkClient
from .models import WorkRequest
from .clients.calendar import CalendarClient
from .clients.memory import MemoryClient
import os
from .clients.acceptance import AcceptanceClient
from .models import AcceptanceRequest 
from .utils.pending_memory import pop_pending
import logging
import logging
import traceback

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
    sheet_url = req.sheet_url or os.getenv("SHEET_URL")
    client = HealthClient()
    try:
        match req.mode:
            case "latest":
                data = await client.latest() 
            case "compare":
                data = await client.compare()
            case "period":
                data = await client.period(req.start_date, req.end_date) 
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

# ---------- Work ----------
@app.post("/work")
async def work_api(req: WorkRequest):
    client = WorkClient()
    try:
        if req.mode == "latest":
            data = await client.latest()

        elif req.mode == "today":
            data = await client.today()

        else:  # "period"
            data = await client.period(req.start_date, req.end_date)

        return data or {"status": "ok", "message": "該当データなし"}

    except Exception as e:
        logging.error("work_api failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="internal error")


@app.post("/functions/get_work_data", tags=["functions"])
async def work_alias(req: WorkRequest):
    return await work_api(req)

# ---------- Acceptance ----------
@app.post("/acceptance")
async def acceptance_api(req: AcceptanceRequest):
    client = AcceptanceClient()
    try:
        if req.mode == "latest":
            data = await client.latest()
        else:
            data = await client.period(req.start_date, req.end_date)
        return data
    except Exception as e:
        logging.exception("acceptance_api failed")
        raise HTTPException(status_code=500, detail=str(e))

# OpenAPI alias
@app.post("/functions/get_acceptance_data", tags=["acceptance"])
async def acceptance_alias(req: AcceptanceRequest):
    return await acceptance_api(req)

# ---------- Calendar ----------
@app.post("/calendar")
async def calendar_api(req: CalendarRequest):
    client = CalendarClient()
    try:
        match req.action:
            case "insert":
                data = await client.insert_event(          # ← await 追加
                    req.summary, req.start, req.end
                )
            case "get":
                data = await client.get_events(            # ← await
                    req.start, req.end
                )
            case "update":
                data = await client.update_event(          # ← await
                    req.event_id, req.summary, req.start, req.end
                )
            case "delete":
                data = await client.delete_event(req.event_id)  # ← await
        return data or {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
# OpenAPI alias
@app.post("/functions/calendar_event", tags=["functions"])
async def calendar_event_alias(req: CalendarRequest):
    return await calendar_api(req)

# ---------- Memory ----------
@app.post("/memory", tags=["memory"])
async def memory_api(req: MemoryRequest):
    page = await MemoryClient().create_record(req.model_dump())
    return {"inserted": page["id"]}

@app.post("/functions/create_memory", tags=["functions"])
async def create_memory_fn(req: MemoryRequest):
    return await memory_api(req)

# ---------- Memory confirm ----------
@app.post("/memory", tags=["memory"])
async def memory_api(req: MemoryRequest):
    if not summary:
        raise HTTPException(404, "no pending memory")
    payload = build_memory_payload(summary)
    page = await MemoryClient().create_record(payload)
    return {"inserted": page["id"]}

@app.post("/functions/get_memory", tags=["functions"])
async def get_memory_alias(req: MemorySearchRequest):
    try:
        result = await MemoryClient().search(req.query, req.top_k)
        return {"status": "success", "data": result}
    except Exception as e:
        logging.exception("memory_search failed:")
        raise HTTPException(status_code=500, detail=str(e))

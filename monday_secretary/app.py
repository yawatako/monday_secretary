"""
FastAPI entrypoint for Render web service.
Exposes:
  GET  /healthcheck   – liveness probe
  POST /chat          – proxy to main_handler.handle_message
  POST /health        – 体調データ取得
  POST /calendar      – カレンダー操作
  POST /memory        – Notion に記憶保存
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from .main_handler import handle_message
from .models import (
    HealthRequest,
    CalendarRequest,
    MemoryRequest,
    MemorySearchRequest,
)
from .clients.health import HealthClient
from .clients.work import WorkClient
from .models import WorkRequest
from .clients.calendar import CalendarClient
from .clients.memory import MemoryClient
import os
import logging
import traceback

logger = logging.getLogger(__name__)

app = FastAPI(title="Monday Secretary API")


async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled error")
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


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
                data = await client.daily_summary(req.start_date or client.today)
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


# ---------- Calendar ----------
@app.post("/calendar")
async def calendar_api(req: CalendarRequest):
    client = CalendarClient()
    try:
        match req.action:
            case "insert":
                data = await client.insert_event(  # ← await 追加
                    req.summary, req.start, req.end
                )
            case "get":
                data = await client.get_events(req.start, req.end)  # ← await
            case "update":
                data = await client.update_event(  # ← await
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
    payload = req.model_dump()
    payload.setdefault("category", "その他")
    payload.setdefault("emotion", "嬉しい")
    payload.setdefault("reason", "")
    page = await MemoryClient().create_record(payload)
    return {"inserted": page["id"]}


@app.post("/functions/create_memory", tags=["functions"])
async def create_memory_fn(req: MemoryRequest):
    return await memory_api(req)


# ---------- Memory search ----------
@app.post("/functions/get_memory", tags=["functions"])
async def get_memory_alias(req: MemorySearchRequest):
    try:
        result = await MemoryClient().search(req.query, req.top_k)
        return {"status": "success", "data": result}
    except Exception as e:
        logging.exception("memory_search failed:")
        raise HTTPException(status_code=500, detail=str(e))

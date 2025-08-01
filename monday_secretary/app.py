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
from google_auth_oauthlib.flow import Flow
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Literal

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
from .clients.tasks import TasksClient
import os
import logging
import traceback

from google_auth_oauthlib.flow import Flow
import os, json

logger = logging.getLogger(__name__)

app = FastAPI(title="Monday Secretary API")


async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled error")
    return JSONResponse(status_code=500, content={"detail": str(exc)})


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.exception("validation error")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# ---------- Chat (既存) ----------
class ChatRequest(BaseModel):
    user_msg: str


class TaskRequest(BaseModel):
    action: Literal["add", "complete", "list"]
    title: str | None = None
    tags: list[str] | None = None
    due: str | None = None
    task_id: str | None = None


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
        logger.exception("health_api failed")
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
        logger.exception("calendar_api failed")
        raise HTTPException(status_code=500, detail=str(e))


# OpenAPI alias
@app.post("/functions/calendar_event", tags=["functions"])
async def calendar_event_alias(req: CalendarRequest):
    return await calendar_api(req)


# ---------- Memory ----------
@app.post("/memory", tags=["memory"])
async def memory_api(req: MemoryRequest):
    payload = req.model_dump()
    if not payload.get("category"):
        payload["category"] = "その他"
    if not payload.get("emotion"):
        payload["emotion"] = "嬉しい"
    if not payload.get("reason"):
        payload["reason"] = ""
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


# ---------- Tasks ----------
@app.post("/tasks", tags=["tasks"])
async def tasks_api(req: TaskRequest):
    client = TasksClient()
    try:
        match req.action:
            case "add":
                task = await client.add_task(req.title or "", req.tags, req.due)
                return {"status": "success", "task": task}
            case "complete":
                task_id = req.task_id
                if not task_id and req.title:
                    found = await client.find_task_by_title(req.title)
                    task_id = found.get("id") if found else None
                if not task_id:
                    return {"status": "error", "detail": "task not found"}
                task = await client.complete_task(task_id)
                return {"status": "success", "task": task}
            case "list":
                raw_tasks = await client.list_tasks()
                tasks = []
                for t in raw_tasks:
                    notes = t.get("notes", "")
                    tags = [w[1:] for w in notes.split() if w.startswith("#")]
                    status = "done" if t.get("status") == "completed" else "pending"
                    tasks.append(
                        {
                            "title": t.get("title", ""),
                            "tags": tags,
                            "due": t.get("due"),
                            "status": status,
                            "created_at": t.get("updated"),
                            "completed_at": t.get("completed"),
                        }
                    )
                return {"status": "success", "tasks": tasks}
    except Exception as e:
        logging.exception("tasks_api failed")
        raise HTTPException(status_code=500, detail=str(e))


# ---------- OAuth2 Callback ----------
@app.get("/oauth2callback")
async def oauth2callback(request: Request):
    # ── 1) env から値を取得 ─────────────────
    client_id     = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    redirect_uri  = "https://health-api-server.onrender.com/oauth2callback"
    token_uri     = "https://oauth2.googleapis.com/token"
    auth_uri      = "https://accounts.google.com/o/oauth2/auth"

    if not (client_id and client_secret):
        return JSONResponse(status_code=500,
                            content={"detail": "env var missing: GOOGLE_OAUTH_CLIENT_ID / _SECRET"})

    # ── 2) Flow を正しい形で構築 ─────────────
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": auth_uri,
            "token_uri": token_uri,
            "redirect_uris": [redirect_uri]
        }
    }

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=["https://www.googleapis.com/auth/tasks"],
        redirect_uri=redirect_uri,
    )

    # ── 3) トークン交換 ─────────────────────
    try:
        flow.fetch_token(code=request.query_params.get("code"))
    except Exception as e:
        return JSONResponse(status_code=400,
                            content={"detail": str(e)})
    
    refresh_token = flow.credentials.refresh_token
    if not refresh_token:
        return JSONResponse(status_code=400, content={"detail": "no refresh_token returned"})

"""
FastAPI entrypoint for Render web service.
Exposes:
  GET /healthcheck  – liveness probe
  POST /chat        – proxy to main_handler.handle_message
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .main_handler import handle_message

app = FastAPI(title="Monday Secretary API")


class ChatRequest(BaseModel):
    user_msg: str


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        response = await handle_message(req.user_msg)
        return {"reply": response}
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(e))

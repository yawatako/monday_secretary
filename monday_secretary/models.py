from datetime import date, datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


# ---------- 体調 ----------
class HealthRequest(BaseModel):
    sheet_url: Optional[str] = None
    mode: Literal["latest", "compare", "period", "dailySummary"] = "latest"
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ---------- 業務 ----------
class WorkRequest(BaseModel):
    mode: Literal["latest", "period"] = "latest"
    start_date: Optional[date] = None
    end_date: Optional[date] = None



# ---------- カレンダー ----------
class CalendarRequest(BaseModel):
    action: Literal["insert", "get", "update", "delete"]
    calendar_id: Optional[str] = None
    summary: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    event_id: Optional[str] = None


# ---------- 記憶 ----------
class MemoryRequest(BaseModel):
    title: str
    summary: str
    category: Optional[str] = None
    emotion: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class MemorySearchRequest(BaseModel):
    query: str = ""  # 空なら最新順
    top_k: int = 5  # 何件返すか


# ---------- Tasks ----------
class Task(BaseModel):
    title: str
    tags: list[str] = []
    due: Optional[str] = None
    status: Literal["pending", "done"] = "pending"
    created_at: datetime
    completed_at: Optional[datetime] = None

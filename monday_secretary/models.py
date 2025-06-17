# monday_secretary/models.py  修正版
from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

# ---------- 体調 ----------
class HealthRequest(BaseModel):
    sheet_url: Optional[str] = None
    mode: Literal["latest", "compare", "period", "dailySummary"] = "latest"
    start_date: Optional[date] = None
    end_date:   Optional[date] = None

# ---------- 業務 ----------
class WorkRequest(BaseModel):
    mode: Literal["latest", "period"] = "latest"
    start_date: Optional[date] = None
    end_date:   Optional[date] = None

# ---------- 自己受容 ----------
class AcceptanceRequest(BaseModel):
    mode: Literal["latest", "period"] = "latest"
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# ---------- カレンダー ----------
class CalendarRequest(BaseModel):
    action: Literal["insert", "get", "update", "delete"]
    calendar_id: Optional[str] = None
    summary:     Optional[str] = None
    start:       Optional[datetime] = None
    end:         Optional[datetime] = None
    event_id:    Optional[str] = None

# ---------- 記憶 ----------
class MemoryRequest(BaseModel):
    title: str
    summary: str
    category: Literal[
        "スケジュール", "創作", "体調", "仕事", "遊び",
        "思い出", "感情", "思考", "その他"
    ]
    emotion: Literal["嬉しい", "悲しい", "怒り", "楽しい", "悔しい", "辛い"]
    reason: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

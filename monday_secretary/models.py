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


# ---------- Acceptance（自己受容） ----------
class AcceptanceRequest(BaseModel):
    mode: Literal["latest", "period"]
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AcceptanceItem(BaseModel):
    タイムスタンプ: date
    今の気持ち: str
    一番印象的だった感情: str
    今日浮かんだ思考の断片: Optional[str] = None
    今日の自分にかけたい言葉: Optional[str] = None
    今日_自分を受け入れられた_瞬間はある: Optional[str] = None
    書き残しておきたいこと: Optional[str] = None


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
    category: str = ""
    emotion: str = ""
    reason: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class MemorySearchRequest(BaseModel):
    query: str = ""  # 空なら最新順
    top_k: int = 5  # 何件返すか

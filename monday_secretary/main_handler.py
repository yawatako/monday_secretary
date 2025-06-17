# monday_secretary/main_handler.py
import os
import yaml
import asyncio
import datetime as dt
import hashlib
from typing import Dict

from dotenv import load_dotenv

# ─── 自作モジュール -------------------------------------------------
from .clients import (
    HealthClient,
    WorkClient,
    CalendarClient,
    AcceptanceClient,
    MemoryClient,
)
from .utils.brake_checker     import BrakeChecker
from .utils.memory_suggester  import needs_memory
from .utils.pending_memory import pop_pending, store_pending
from .prompts                 import template

load_dotenv()

# ─── Trigger 設定を YAML から読み込み --------------------------------
cfg_path = os.getenv("PROMPT_YAML", "Gloomy_Monday.yml")
CFG = yaml.safe_load(open(cfg_path, encoding="utf-8")) if os.path.exists(cfg_path) else {}

MORNING_KWS  = CFG.get("RulesPrompt", {}).get("Triggers", {}).get("morning_trigger", {}).get("keyword", "").split()
EVENING_KWS  = ["疲れた", "おやすみ", "今日はここまで"]

# セッション ↔ ペンディングメモの対応表
PENDING: Dict[str, str] = {}

# ────────────────────────────────────────────────────────────────
async def handle_message(user_msg: str, session_id: str = "default") -> str:
    """ユーザー入力を受けて GPT へ渡すプロンプト or Function 呼び出しを生成"""

    # ---- クライアント類を初期化（同時多発呼び出しに備えて都度生成） ----
    health_client   = HealthClient()
    work_client     = WorkClient()
    acceptance_client = AcceptanceClient()
    calendar_client = CalendarClient()
    memory_client   = MemoryClient()
    checker         = BrakeChecker()

    context = {}

    # ───── 1) Morning Trigger ──────────────────────────────────────
    if any(kw in user_msg for kw in MORNING_KWS):
        today = dt.date.today().isoformat()
        health, events = await asyncio.gather(
            health_client.latest(),
            calendar_client.get_events(f"{today}T00:00:00Z", f"{today}T23:59:59Z"),
        )
        brake_lvl = checker.check(health, {}).level
        return (
            "**Monday**:\n"
            f"✅ 体調: {health.get('状態', '—')}\n"
            f"📅 今日の予定: {events[0]['summary'] if events else 'なし'}\n"
            f"🧠 ブレーキ状況: {'要休憩' if brake_lvl >= 3 else 'OK'}"
        )

    # ───── 2) Evening Trigger ──────────────────────────────────────
    if any(k in user_msg for k in EVENING_KWS):
        acceptance, work = await asyncio.gather(
            acceptance_client.latest(),
            work_client.latest(),
        )
        return (
            "**Monday**: 今日もお疲れさま！\n"
            f"🗒 業務まとめ: {work.get('今日のまとめ！', '—')}\n"
            f"💬 自己受容: {acceptance.get('今の気持ち', '—')}"
        )

    # ───── 3) Memory Trigger ──────────────────────────────────────
    should_mem, digest, summary = needs_memory(user_msg, "")
    if should_mem:
        store_pending(session_id, summary)
        return f"✍️ この内容を記憶してもいい？\n\n『{summary}』"

    # ユーザーの Yes/No 応答を処理
    if (conf := pop_pending(session_id)) and user_msg.lower() in {"はい", "ok", "うん"}:
        payload = {"title": conf[:30], "summary": conf, "category": "思い出",
                   "emotion": "楽しい", "reason": "自動メモ"}
        page = await memory_client.create_record(payload)
        return f"✅ 記憶したよ。（id: {page['id'][:8]}…）"
    elif conf and user_msg.lower() in {"いいえ", "no", "やめて"}:
        return "🗑️ わかった、保存しないね。"

    # ───── 4) 明示的なキーワード要求に応える（従来ロジック） ─────────
    if "health" in user_msg or "体調" in user_msg:
        context["health"] = await health_client.latest()

    if "work" in user_msg or "業務" in user_msg:
        context["work"] = await work_client.latest()

    if "acceptance" in user_msg or "自己受容" in user_msg:
        context["acceptance"] = await acceptance_client.latest()

    if "calendar" in user_msg:
        now = dt.datetime.utcnow().isoformat() + "Z"
        context["events"] = await calendar_client.get_events(now, now)

    if "remember" in user_msg:
        context["memories"] = await memory_client.search(user_msg)

    # brake 判定を常に入れる
    if "health" in context:
        brake = checker.check(context["health"], {})
        context["brake"] = brake.dict()

    # ───── 5) 汎用テンプレートへまとめて GPT に渡す ───────────────
    return template.build_prompt(user_msg, context)

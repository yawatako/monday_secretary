import os
import yaml
import asyncio
import datetime
from dotenv import load_dotenv

from .clients import HealthClient, CalendarClient, MemoryClient, WorkClient
from .utils import BrakeChecker
from .prompts import template
from .utils.memory_suggester import needs_memory

load_dotenv()

# ───────────────────────────────────────────────────────────────
# YAML で定義した Triggers を読み込む (例: Gloomy_Monday.yml)
cfg_path = os.getenv("PROMPT_YAML", "Gloomy_Monday.yml")
if os.path.exists(cfg_path):
    CFG = yaml.safe_load(open(cfg_path, encoding="utf-8"))
else:
    CFG = {}
MORNING_KWS = (
    CFG.get("RulesPrompt", {})
       .get("Triggers", {})
       .get("morning_trigger", {})
       .get("keyword", "")
       .split()
)

# ───────────────────────────────────────────────────────────────
async def handle_message(user_msg: str, session_id: str | None = None) -> str:
    """ユーザー入力を受けて GPT へ渡す最終プロンプト (または Function 呼び出し) を生成"""
    health_client   = HealthClient()
    work_client     = WorkClient()
    calendar_client = CalendarClient()
    memory_client   = MemoryClient()
    checker         = BrakeChecker()

    # ── 1) morning_trigger か判定 ────────────────────────
    if any(kw in user_msg for kw in MORNING_KWS):
        today = datetime.date.today().isoformat()
        health, events = await asyncio.gather(
            health_client.latest(),
            calendar_client.get_events(f"{today}T00:00:00Z", f"{today}T23:59:59Z"),
        )
        brake_lvl = checker.check(health, {}).level
        summary = (
            "**Monday**:\n"
            f"✅ 体調: {health.get('状態', '—')}\n"
            f"📅 今日の予定: {events[0]['summary'] if events else 'なし'}\n"
            f"🧠 ブレーキ状況: {'要休憩' if brake_lvl >= 3 else 'OK'}"
        )
        return summary

    # ── 1) evening_trigger か判定 ────────────────────────
    if any(k in user_msg for k in ["疲れた", "おやすみ", "今日はここまで"]):
        acceptance = await acceptance_client.latest()
        work       = await work_client.latest()
        context.update({"acceptance": acceptance, "work": work})

    # ---------- Memory trigger 判定 ----------
    if needs_memory(user_msg):
        # 140 文字要約
        summary = summarize_for_memory(user_msg)
        _store_pending(session_id, summary)  # dict / redis 等へ
        return f"✍️ この内容を記憶してもいい？\n\n『{summary}』"
    
    if "health" in user_msg or "体調" in user_msg:
        health = await health_client.latest()
        context["health"] = health

    if "work" in user_msg or "業務" in user_msg:
        work = await work_client.latest()
        context["work"] = work

    if "calendar" in user_msg:
        now = datetime.datetime.utcnow().isoformat() + "Z"
        events = await calendar_client.get_events(now, now)
        context["events"] = events

    if "remember" in user_msg:
        results = await memory_client.search(user_msg)
        context["memories"] = results

    brake = checker.check(health, {})
    context["brake"] = brake.dict()

    prompt = template.build_prompt(user_msg, context)
    return prompt


# ───────────────────────────────────────────────────────────────
def main() -> None:
    import sys

    user_msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "おはよう"
    output = asyncio.run(handle_message(user_msg))
    print(output)


if __name__ == "__main__":
    main()

import os
import yaml
import asyncio
import datetime
from dotenv import load_dotenv

from .clients import HealthClient, CalendarClient, MemoryClient, WorkClient   # ★ WorkClient 追加
from .utils import BrakeChecker
from .prompts import template

load_dotenv()

# ───────────────────────────────────────────────────────────────
# YAML で定義した Triggers を読み込む  (例: Gloomy Monday.yml)
CFG = yaml.safe_load(open(os.getenv("PROMPT_YAML", "Gloomy Monday.yml"), encoding="utf-8"))
MORNING = CFG.get("Triggers", {}).get("morning_trigger", {})

# ───────────────────────────────────────────────────────────────
async def handle_message(user_msg: str) -> str:
    """ユーザー入力を受けて GPT へ渡す最終プロンプト (または Function 呼び出し) を生成"""
    health_client   = HealthClient()
    work_client     = WorkClient()          # ★ 追加
    calendar_client = CalendarClient()
    memory_client   = MemoryClient()
    checker         = BrakeChecker()

    # ── 1) morning_trigger か判定 ────────────────────────
    if MORNING.get("enabled") and MORNING.get("keyword") in user_msg:
        today_str   = datetime.date.today().isoformat()
        today_start = f"{today_str}T00:00:00Z"
        today_end   = f"{today_str}T23:59:59Z"

        # 体調・業務メモ・今日の予定を並列取得
        health, work, events = await asyncio.gather(
            health_client.latest(),
            work_client.latest(),
            calendar_client.get_events(today_start, today_end),
        )

        brake_level = checker.check(health, {})         # ← 第二引数は activity diff など無ければ空辞書
        prompt = (
            "【朝のリマインド】\n"
            f"■ 体調: {health}\n"
            f"■ 業務メモ: {work}\n"
            f"■ 今日の予定: {events}\n"
            f"■ ブレーキ判定: Level{brake_level.level}\n\n"
            "上記を踏まえ、優しい口調で 5 行以内にまとめてください。"
        )
        return prompt

    # ── 2) 通常フロー (キーワードルーティング) ────────────────
    context: dict[str, any] = {}
    health: dict = {}

    if "health" in user_msg:
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

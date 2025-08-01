import os, yaml, asyncio, datetime as dt
from typing import Dict, List

from dotenv import load_dotenv

# ─── 共通定数 --------------------------------------------------------
# Google Calendar API 用タイムゾーン
JST = dt.timezone(dt.timedelta(hours=9))
TZ_NAME = "Asia/Tokyo"

# ─── 自作モジュール -------------------------------------------------
from .clients import (
    HealthClient,
    WorkClient,
    CalendarClient,
    MemoryClient,
    TasksClient,
)
from .utils.brake_checker import BrakeChecker
from .utils.memory_suggester import needs_memory
from .utils.pending_memory import pop_pending, store_pending
from .prompts import template

load_dotenv()

# ─── Trigger 設定を YAML から読み込み ------------------------------
cfg_path = os.getenv("PROMPT_YAML", "Gloomy Monday.yml")
CFG = (
    yaml.safe_load(open(cfg_path, encoding="utf-8")) if os.path.exists(cfg_path) else {}
)

MORNING_KWS = (
    CFG.get("RulesPrompt", {})
    .get("Triggers", {})
    .get("morning_trigger", {})
    .get("keywords", [])
)
EVENING_KWS = (
    CFG.get("RulesPrompt", {})
    .get("Triggers", {})
    .get("evening_trigger", {})
    .get("keywords", [])
)
WEEKEND_KWS = (
    CFG.get("RulesPrompt", {})
    .get("Triggers", {})
    .get("weekend_trigger", {})
    .get("keywords", [])
)
REMEMBER_KWS = ["覚えてる？", "思い出して", "あの時の記憶", "過去メモ"]

# セッション ↔ ペンディングメモ
PENDING: Dict[str, str] = {}
# 朝トリガーのロックとタイムスタンプ
MORNING_LOCKS: Dict[str, asyncio.Lock] = {}
LAST_MORNING: Dict[str, dt.datetime] = {}

# ────────────────────────────────────────────────────────────────
async def handle_message(user_msg: str, session_id: str = "default") -> str:
    """ユーザー入力を受けて GPT へ渡すプロンプト／Function 呼び出しを生成"""

    # 各クライアントを初期化
    health_client = HealthClient()
    work_client = WorkClient()
    calendar_client = CalendarClient()
    memory_client = MemoryClient()
    checker = BrakeChecker()

    context = {}

    # ===== 0) remember_trigger =========================================
    if any(kw in user_msg for kw in REMEMBER_KWS):
        # 直近 5 件を時系列降順で取得 → Markdown 整形
        results: List[dict] = await memory_client.search("")  # ← 空クエリ＝最新順
        if not results:
            return "**Monday**：まだ何も記憶がないみたい… 🤔"

        lines = []
        for pg in results:  # Notion API のレスポンス想定
            props = pg["properties"]
            title = props["title"]["title"][0]["plain_text"]
            created = pg["created_time"][:10]
            url = pg["url"]
            cat = props["category"]["select"]["name"]
            lines.append(f"- **{title}**（{created} / {cat}）\n  {url}")

        return "**Monday**：こんなメモがあるよ 📚\n\n" + "\n".join(lines)

    # ── morning_trigger ──────────────────────────────────────────
    if any(kw in user_msg for kw in MORNING_KWS):
        state = MORNING_LOCKS.setdefault(session_id, asyncio.Lock())
        last = LAST_MORNING.get(session_id)
        now = dt.datetime.utcnow()
        if state.locked():
            return "⏳ 朝のサマリーを生成中だよ。少し待ってね。"
        if last and (now - last).total_seconds() < 600:
            # 10 分以内の再実行は禁止（前回結果を返す）
            return "🔄 さっき結果を返したばかりだよ。また少し経ってから試してね。"

        async with state:
            LAST_MORNING[session_id] = now

            tz = dt.timezone(dt.timedelta(hours=9))
            today = dt.datetime.now(tz).date()
            start_iso = dt.datetime.combine(today, dt.time.min, tz).isoformat()
            end_iso = dt.datetime.combine(today, dt.time.max, tz).isoformat()

            # Health・Calendar を並列取得
            health, events = await asyncio.gather(
            health_client.latest(),
            calendar_client.get_events(start_iso, end_iso, "Asia/Tokyo"),
            )

            # ① 体調詳細を組み立て
            sleep = health.get("睡眠時間")
            slept_w = "ぐっすり" if health.get("slept_well") else "浅め"
            stomach = health.get("胃腸")
            mood = health.get("気分")

            if sleep is not None:
                health_line = f"睡眠 {sleep}h（{slept_w}）／胃腸 {stomach or '—'}／気分 {mood or '—'}"
            else:
                health_line = health.get("状態", "—")

            # ② 予定を箇条書き（なければ “なし”）
            if events:
                lines = []
                for e in events:
                    start = e.get("start", {})
                    summary = e.get("summary", "（無題）")

                    # dateTime（時間指定）か date（終日）かで分岐
                    start_time = start.get("dateTime")
                    start_date = start.get("date")

                    if start_time:
                        time_text = start_time[11:16] + "〜"
                    elif start_date:
                        time_text = "終日"
                    else:
                        time_text = "？"

                    lines.append(f"　・{summary}（{time_text}）")
                today_events = "\n".join(lines)
            else:
                today_events = "　（登録なし。フリータイム！）"

            # ③ ブレーキ判定
            brake_lvl = checker.check(health, {}).level
            brake_text = {
                0: "余裕あり",
                1: "普通",
                2: "注意",
                3: "休憩優先",
                4: "強制休憩",
            }[brake_lvl]

            # ④ メッセージ生成
            summary = (
                "**Monday**：おはよう！ 今朝の状態をまとめるね。\n\n"
                "### 🩺 体調\n"
                f"{health_line}\n\n"
                "### 📅 今日の予定\n"
                f"{today_events}\n\n"
                "### 🛑 ブレーキポイント\n"
                f"　・現在レベル **{brake_lvl}**（{brake_text}）\n"
                "　・胃腸が不安なら、温かい飲み物＋軽いストレッチを優先。\n\n"
                "### 💡 Monday のアドバイス\n"
                "やることを 3 つまでに絞って、合間に 5 分の休憩を入れてみて。\n"
                "まずは **『体を起こす → 水分 → 軽い準備運動』** の順でスタートしよう！"
            )
            LAST_MORNING[session_id] = dt.datetime.utcnow()
            return summary

    # ──────────── 2) evening_trigger ───────────────
    if any(k in user_msg for k in EVENING_KWS):
        work_today = await work_client.today()
        return (
            "**Monday**：今日もお疲れさま！\n"
            f"🗒 **業務まとめ**：{work_today.get('今日のまとめ！', '—') if work_today else '（記録なし）'}"
        )

    # ──────────── 2.5) weekend_trigger ─────────────
    if any(k in user_msg for k in WEEKEND_KWS):
        tz = dt.timezone(dt.timedelta(hours=9))
        today = dt.datetime.now(tz).date()
        start = today - dt.timedelta(days=today.weekday())
        end = today

        tasks, events, health_logs, work_logs = await asyncio.gather(
            TasksClient().list_tasks(),
            CalendarClient().get_events(
                f"{start}T00:00:00+09:00", f"{end}T23:59:59+09:00", "Asia/Tokyo"
            ),
            HealthClient().period(start, end),
            WorkClient().period(start, end),
        )

        grouped: Dict[str, List[str]] = {}
        for t in tasks:
            notes = t.get("notes", "")
            tags = [w[1:] for w in notes.split() if w.startswith("#")]
            if not tags:
                tags = ["その他"]
            line = f"- {t.get('title')} ({t.get('due', '-')[:10]})"
            for tag in tags:
                grouped.setdefault(tag, []).append(line)

        task_lines: List[str] = []
        for tag, lines in grouped.items():
            task_lines.append(f"#### {tag}")
            task_lines.extend(lines)

        event_lines = []
        for e in events:
            st = e.get("start", {})
            date_text = st.get("dateTime", st.get("date", ""))[:10]
            event_lines.append(f"- {e['summary']} ({date_text})")
        if not event_lines:
            event_lines.append("- （イベントなし）")

        health_lines = []
        for r in health_logs:
            mood = r.get("気分", "-")
            sleep = r.get("睡眠時間", "-")
            d = r.get("タイムスタンプ", "")[:10]
            health_lines.append(f"- {d} 気分:{mood} 睡眠:{sleep}h")
        if not health_lines:
            health_lines.append("- （記録なし）")

        work_lines = []
        for r in work_logs:
            d = r.get("タイムスタンプ", "")[:10]
            memo = r.get("今日のまとめ！", "-")
            work_lines.append(f"- {d} {memo}")
        if not work_lines:
            work_lines.append("- （記録なし）")

        summary = (
            "**Monday**：週末整理の時間だよ。\n\n"
            "### 📝 未完タスク\n"
            + "\n".join(task_lines or ["- （なし）"])
            + "\n\n### 📅 実行済イベント\n"
            + "\n".join(event_lines)
            + "\n\n### 🩺 健康ログ\n"
            + "\n".join(health_lines)
            + "\n\n### 🏢 業務メモ\n"
            + "\n".join(work_lines)
        )
        return summary



    # ──────────── 3) Memory Trigger ────────────────
    should_mem, digest, summary = needs_memory(user_msg, "")
    if should_mem:
        store_pending(session_id, summary)
        return f"✍️ この内容を記憶してもいい？\n\n『{summary}』"

    # Yes/No 応答処理
    if (conf := pop_pending(session_id)) and user_msg.lower() in {"はい", "ok", "うん"}:
        payload = {
            "title": conf[:30],
            "summary": conf,
            "category": "思い出",
            "emotion": "楽しい",
            "reason": "自動メモ",
        }
        page = await memory_client.create_record(payload)
        return f"✅ 記憶したよ。（id: {page['id'][:8]}…）"
    elif conf and user_msg.lower() in {"いいえ", "no", "やめて"}:
        return "🗑️ わかった、保存しないね。"

    # ──────────── 4) 明示キーワード応答 ──────────────
    if "health" in user_msg or "体調" in user_msg:
        context["health"] = await health_client.latest()

    if "work" in user_msg or "業務" in user_msg:
        context["work"] = await work_client.latest()


    if "calendar" in user_msg:
        tz = dt.timezone(dt.timedelta(hours=9))
        now = dt.datetime.now(tz)
        start_iso = now.isoformat(timespec="seconds")
        end_iso = (now + dt.timedelta(days=1)).isoformat(timespec="seconds")
        context["events"] = await calendar_client.get_events(start_iso, end_iso, "Asia/Tokyo")

    if "remember" in user_msg:
        context["memories"] = await memory_client.search(user_msg)

    # brake 判定を常に入れる
    if "health" in context:
        context["brake"] = checker.check(context["health"], {}).dict()

    # ──────────── 5) GPT 用テンプレート生成 ───────────
    return template.build_prompt(user_msg, context)

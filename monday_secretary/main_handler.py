import os, yaml, asyncio, datetime as dt, hashlib
from typing import Dict

from dotenv import load_dotenv

# ─── 自作モジュール -------------------------------------------------
from .clients import (
    HealthClient, WorkClient, CalendarClient,
    AcceptanceClient, MemoryClient,
)
from .utils.brake_checker      import BrakeChecker
from .utils.memory_suggester   import needs_memory
from .utils.pending_memory     import pop_pending, store_pending
from .prompts                  import template

load_dotenv()

# ─── Trigger 設定を YAML から読み込み ------------------------------
cfg_path = os.getenv("PROMPT_YAML", "Gloomy_Monday.yml")
CFG = yaml.safe_load(open(cfg_path, encoding="utf-8")) if os.path.exists(cfg_path) else {}

MORNING_KWS = CFG.get("RulesPrompt", {}).get("Triggers", {})\
                 .get("morning_trigger", {}).get("keyword", "").split()
EVENING_KWS = ["疲れた", "おやすみ", "今日はここまで"]

# セッション ↔ ペンディングメモ
PENDING: Dict[str, str] = {}

# ────────────────────────────────────────────────────────────────
async def handle_message(user_msg: str, session_id: str = "default") -> str:
    """ユーザー入力を受けて GPT へ渡すプロンプト／Function 呼び出しを生成"""

    # 各クライアントを初期化
    health_client     = HealthClient()
    work_client       = WorkClient()
    acceptance_client = AcceptanceClient()
    calendar_client   = CalendarClient()
    memory_client     = MemoryClient()
    checker           = BrakeChecker()

    context = {}

  # ── morning_trigger ──────────────────────────────────────────
    if any(kw in user_msg for kw in MORNING_KWS):
      today = datetime.date.today().isoformat()
      start_iso, end_iso = f"{today}T00:00:00Z", f"{today}T23:59:59Z"

      # Health・Calendar を並列取得
      health, events = await asyncio.gather(
          health_client.latest(),
          calendar_client.get_events(start_iso, end_iso),
      )

      # ① 体調詳細を組み立て
      sleep   = health.get("睡眠時間", "—")
      slept_w = "ぐっすり" if health.get(" slept_well") else "浅め"
      stomach = health.get("胃腸", "—")
      mood    = health.get("気分", "—")

      health_line = (
          f"睡眠 {sleep}h（{slept_w}）／胃腸 {stomach}／気分 {mood}"
          if sleep != "—" else "—"
      )

      # ② 予定を箇条書き（なければ “なし”）
      if events:
          today_events = "\n".join(f"　・{e['summary']}（{e['start']['dateTime'][11:16]}〜）"
                                   for e in events)
      else:
          today_events = "　（登録なし。フリータイム！）"

      # ③ ブレーキ判定
      brake_lvl  = checker.check(health, {}).level
      brake_text = {0: "余裕あり", 1: "普通", 2: "注意", 3: "休憩優先", 4: "強制休憩"}[brake_lvl]

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
      return summary

  # ──────────── 2) evening_trigger ─────────────── 
    if any(k in user_msg for k in EVENING_KWS):
        today_acceptance = await acceptance_client.today()
        work_today       = await work_client.today()   # WorkClient も同様に today() を実装している想定
        return (
            "**Monday**：今日もお疲れさま！\n"
            f"🗒 **業務まとめ**：{work_today.get('今日のまとめ！', '—') if work_today else '（記録なし）'}\n"
            f"💬 **自己受容**：{today_acceptance.get('今の気持ち', '—') if today_acceptance else '（記録なし）'}"
        )

    # ──────────── 3) Memory Trigger ────────────────
    should_mem, digest, summary = needs_memory(user_msg, "")
    if should_mem:
        store_pending(session_id, summary)
        return f"✍️ この内容を記憶してもいい？\n\n『{summary}』"

    # Yes/No 応答処理
    if (conf := pop_pending(session_id)) and user_msg.lower() in {"はい", "ok", "うん"}:
        payload = {
            "title": conf[:30], "summary": conf,
            "category": "思い出", "emotion": "楽しい", "reason": "自動メモ"
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

    if "acceptance" in user_msg or "自己受容" in user_msg:
        context["acceptance"] = await acceptance_client.latest()

    if "calendar" in user_msg:
        now_iso = dt.datetime.utcnow().isoformat() + "Z"
        context["events"] = await calendar_client.get_events(now_iso, now_iso)

    if "remember" in user_msg:
        context["memories"] = await memory_client.search(user_msg)

    # brake 判定を常に入れる
    if "health" in context:
        context["brake"] = checker.check(context["health"], {}).dict()

    # ──────────── 5) GPT 用テンプレート生成 ───────────
    return template.build_prompt(user_msg, context)

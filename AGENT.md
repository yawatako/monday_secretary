# 🗂️ Monday Secretary – Agent Design Brief  
updated : 2025-06-18 (JST)

---

## 1. Mission

**「体調・感情・予定の一元管理」**  
会話ベースで  
1. **記録**（Google Sheets／Notion／Google Calendar へ書き込み）  
2. **検索・要約**（朝・夜トリガー／期間検索／検索語リクエスト）  
3. **行動提案**（ブレーキ判定・休憩提案）  
を実現するフルスタック Chat-Agent 群のハブ。

---

## 2. Current Layers

| Layer | Dir/File | 主な責務 | 外部 |
|-------|----------|----------|------|
| **API Gateway** | `app.py` / `openapi.yaml` | ① `/functions/*` を GPT Action として公開<br>② `/chat` -> `main_handler` | Render |
| **Orchestrator** | `main_handler.py` | トリガー判定・クライアント呼び出し・返信生成 | – |
| **Clients** | `clients/*.py` | Sheets / Calendar / Notion アクセス (非同期) | Google / Notion |
| **Utils** | `utils/*.py` | 日付変換・ブレーキ判定・メモ提案 | – |
| **Prompts / Rules** | `Gloomy_Monday.yml`, `prompts/template.py` | LLM 指令・フォーマット | – |

---

## 3. Open Issues (2025-06-18)

| ID | 症状 | 原因 (推定) | 影響 |
|----|------|-------------|------|
| **P-1** Memory Trigger → **422** | `MemoryRequest` schema とコード渡し payload が乖離 | メモ保存不可 |
| **P-2** Health period → **TypeError** | row 文字列日付を `date` へ変換前に比較 | 期間取得不能 |
| **P-3** Storage API Regression | バリデーション強化により古い payload が弾かれる | 不定期失敗 |
| **P-4** ログ不足 | Validation / Retry が stack trace を握り潰す | 原因調査困難 |

---

## 4. Immediate FIX Tasks ✅

| Pri | Task | File | Hint |
|-----|------|------|------|
| 🔴 | **T-1**: `MemoryRequest` を **title+summary だけ必須**へ緩和 or `main_handler` でデフォルト付与 | `models.py`, `app.py` | unblock P-1 |
| 🟠 | **T-2**: `HealthClient.period()` – `_to_date()` で比較 | `clients/health.py` | fix P-2 |
| 🟠 | **T-3**: グローバル例外 + `RequestValidationError` ハンドラ | `app.py` | surface P-4 |
| 🟡 | **T-4**: `openapi.yaml` **Memory** path に Example payload 追加 | `openapi.yaml` | align GPT |

---

## 5. Trigger Spec

| Trigger | キーワード | 動作 |
|---------|------------|------|
| **morning_trigger** | YAML: `おはよう` 等 | 今日の体調 / 予定 / ブレーキを Markdown で返す |
| **evening_trigger** | YAML: `仕事終わり` 等 | 当日の業務記録があれば要約して返す |
| **self_acceptance_trigger** | YAML: `自己受容` 等 | 今日の自己受容メモを要約して返す |
| **memory_trigger** | needs_memory() が True | 要約を提示 → ユーザ承認で Notion 保存 |
| **remember_trigger** | ex. `覚えてる？`, `◯◯のメモ` | (todo) Notion 過去7d 検索 & 上位3件 |

キーワードリストは **`Gloomy_Monday.yml`** に集約する。

---

## 6. Schemas (After Fix)

### 6.1 MemoryRequest (Notion `/v1/pages`)

```jsonc
{
  "parent": { "database_id": "210de35a02a7801e92a5eaeedccfc03e" },
  "properties": {
    "タイトル":  { "title": [{ "text": { "content": "寝落ち日記" } }] },
    "要約":      { "rich_text": [{ "text": { "content": "ベッドで即寝" } }] },

    // ↓ 以下は **optional** 扱い
    "カテゴリ":  { "select": { "name": "体調" } },
    "感情":      { "select": { "name": "嬉しい" } },
    "理由":      { "rich_text": [{ "text": { "content": "記録用" } }] }
  }
}

### 6.2 HealthRequest (period)
{
  "mode": "period",
  "start_date": "2025-06-10",
  "end_date":   "2025-06-17"
}

## 7. ENV Vars
|name | example | note|
|GOOGLE_SA_JSON_PATH | /etc/creds/sa.json | |
|SHEET_URL | Google Sheet (3 tabs) | |
|GOOGLE_REFRESH_TOKEN, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET | Calendar | |
|NOTION_TOKEN | secret_… | |
|NOTION_DB_ID | memories DB | |

## 8. Acceptance Criteria
	•	Morning trigger → 睡眠/胃腸/気分/ブレーキ/予定 を Markdown list で返す
	•	Evening trigger → 今日行が無い場合 “記録なし” と返答
	•	/memory 422 が消える（title+summary 最小）
	•	Health period 正常 slice (unit-test)
	•	すべての失敗 path が FastAPI log に stack-trace を残す

## 9. Roadmap (nice-to-have)
	•	Slack /monday slash-command
	•	PWA dashboard (Chart.js)
	•	Sheets → Postgres ETL after 1 year

---

Next PR should close T-1…T-3 and update docs.
手順: test locally → push → Render auto-deploy → ✅ with GPT Actions.

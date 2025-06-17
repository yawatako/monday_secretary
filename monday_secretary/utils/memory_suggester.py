# monday_secretary/utils/memory_suggester.py
"""
「この対話を Notion に残した方がよさそう？」を判定する簡易ロジック。
パッケージ依存をゼロにして、import エラーを根絶する。
"""

import hashlib
from collections import Counter

# --- チューニングしやすい重み付キーワード ------------------------------
POSITIVE   = {"うれしい": 2, "楽しい": 2, "感謝": 2, "よかった": 1}
NEGATIVE   = {"悲しい": 2, "辛い": 2, "怒り": 2, "疲れた": 1}
REFLECTIVE = {"気づき": 2, "学んだ": 2, "発見": 2, "思った": 1}

THRESHOLD_SCORE = 3        # この値以上なら “記録しよう”


def _score(text: str) -> int:
    """キーワード出現数 × 重み の単純合計"""
    cnt = Counter()
    for w in list(POSITIVE) + list(NEGATIVE) + list(REFLECTIVE):
        if w in text:
            cnt[w] += text.count(w)

    s = 0
    for w, c in cnt.items():
        if w in POSITIVE:
            s += POSITIVE[w] * c
        elif w in NEGATIVE:
            s += NEGATIVE[w] * c
        else:
            s += REFLECTIVE[w] * c
    return s


# -------------------------------------------------------------------------
def needs_memory(user_msg: str, assistant_msg: str) -> tuple[bool, str, str]:
    """
    - True なら「Notion に取っておく？」
    - 返り値: (要否, digest, summary)
    """
    text = f"{user_msg}\n{assistant_msg}"
    score = _score(text)

    if score >= THRESHOLD_SCORE:
        digest  = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
        summary = (
            user_msg[:40] + "…" if len(user_msg) > 40 else user_msg
        )
        return True, digest, summary
    return False, "", ""

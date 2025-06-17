import re, datetime, hashlib
from textblob import TextBlob      # or any JP-sentiment lib

EMO_POS = {"😂", "😍", "😭", "✨", "🎉", "🔥"}
EMO_NEG = {"😢", "😡", "💀"}

REFLECT_PAT  = re.compile(r"(わたし|私|ぼく|俺).{0,10}(感じ|思っ|気づ|学ん|反省)")
NEGATIVE_PAT = re.compile(r"(死にたい|やめたい|消えたい)")

def needs_memory(text: str, history: list[str]) -> bool:
    score = 0

    # 0. NG ワード
    if NEGATIVE_PAT.search(text):
        return False   # 他ルートに回す

    # 1. 感情強度
    emo_plus = len(set(text) & EMO_POS)
    emo_minus= len(set(text) & EMO_NEG)
    score += 2 * (emo_plus + emo_minus)

    polarity = TextBlob(text).sentiment.polarity   # -1..1
    if abs(polarity) > 0.5:
        score += 1

    # 2. 自己リフレクション
    if REFLECT_PAT.search(text):
        score += 1

    # 3. 新規性（ハッシュで簡易重複チェック）
    digest = hashlib.md5(text.encode()).hexdigest()
    if digest not in history:
        score += 1

    # 4. 具体性
    if re.search(r"\d", text):
        score += 1

    # 5. 長さ
    if 20 <= len(text) <= 280:
        score += 1

    # 6. 絵文字/記号
    if text.count("!") >= 3:
        score += 1

    return score >= 3

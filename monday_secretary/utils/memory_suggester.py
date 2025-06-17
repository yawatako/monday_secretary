def needs_memory(user_msg: str) -> bool:
    """キーワードと長さベースの簡易判定"""
    trigger_words = ["覚えて", "メモ", "記録", "残して"]
    if any(w in user_msg for w in trigger_words):
        return True
    if len(user_msg) > 120:       # 長文 → 残したい可能性高
        return True
    return False

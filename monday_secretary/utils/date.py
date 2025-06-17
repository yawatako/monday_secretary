from datetime import date, datetime

def to_date(s: str) -> date:
    """
    '2025/06/18' や '2025-06-18 09:00:00' など → date 型に変換
    """
    return datetime.fromisoformat(s.split()[0].replace("/", "-")).date()

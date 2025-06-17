from datetime import datetime, date

def to_date(s: str | date) -> date:
    """ 'YYYY/MM/DD' や 'YYYY-MM-DD' 文字列 → date 型 """
    if isinstance(s, date):
        return s
    return datetime.fromisoformat(s.replace("/", "-")).date()

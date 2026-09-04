from datetime import date, timedelta


def today_iso() -> str:
    return date.today().isoformat()


def days_ago_iso(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple


def parse_iso_timestamp(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def is_stale(value: str, max_age_minutes: int, now: Optional[datetime] = None) -> Tuple[Optional[bool], Optional[str]]:
    ts = parse_iso_timestamp(value)
    if ts is None:
        return None, "timestamp_parse_failed"
    current = now or datetime.now(timezone.utc)
    age_minutes = (current - ts).total_seconds() / 60
    return age_minutes > max_age_minutes, None

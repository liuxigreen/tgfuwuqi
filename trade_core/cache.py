from __future__ import annotations

import time
from typing import Any, Dict, Tuple


class TTLCache:
    def __init__(self):
        self._data: Dict[str, Tuple[float, Any]] = {}

    def set(self, key: str, value: Any, ttl_seconds: int):
        self._data[key] = (time.time() + ttl_seconds, value)

    def get(self, key: str):
        if key not in self._data:
            return None, False, False
        expiry, value = self._data[key]
        stale = time.time() > expiry
        return value, not stale, stale

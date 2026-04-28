from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def load_events_for_date(date: str, journal_dir='data/trade_core_journal') -> List[Dict]:
    p = Path(journal_dir) / f'{date}.trade_core.jsonl'
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]

from __future__ import annotations

from .models import SkillRecord
from ..config import load_config


def load_skill_registry(config=None):
    cfg = config or load_config()
    items = cfg.get("skill_registry", {}).get("skills", {})
    records = []
    if isinstance(items, list):
        iterable = [(i.get("skill_id", ""), i) for i in items if isinstance(i, dict)]
    else:
        iterable = list(items.items())
    for sid, meta in iterable:
        meta = meta or {}
        records.append(SkillRecord(skill_id=sid, source=meta.get("source", "unknown"), category=meta.get("category", "general"), can_execute_trade=sid == "okx-cex-trade", enabled=sid in {"okx-cex-market", "okx-cex-smartmoney", "nuwa-runtime"}, trusted=meta.get("source") == "official", lifecycle_stages=["pre_trade"]).__dict__)
    return {"skills": records}

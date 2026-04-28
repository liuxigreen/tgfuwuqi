from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class LatencyTracker:
    t0: float = field(default_factory=lambda: time.perf_counter())
    marks: Dict[str, float] = field(default_factory=dict)

    def mark(self, name: str) -> None:
        self.marks[name] = (time.perf_counter() - self.t0) * 1000

    def summary(self) -> Dict[str, float]:
        total = (time.perf_counter() - self.t0) * 1000
        out = {"total_ms": round(total, 2)}
        prev = 0.0
        for k, v in self.marks.items():
            out[f"{k}_ms"] = round(v - prev, 2)
            prev = v
        return out

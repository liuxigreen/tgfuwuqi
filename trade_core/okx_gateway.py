from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import OperatingMode, OrderIntent


class OkxGateway:
    def __init__(self, profile: str = "demo", dry_run: bool = True, allow_live_execution: bool = False):
        self.profile = profile
        self.dry_run = dry_run
        self.allow_live_execution = allow_live_execution
        self.okx_bin = shutil.which("okx")

    def _run_okx_readonly(self, args: List[str]) -> Optional[Dict[str, Any]]:
        if not self.okx_bin:
            return None
        cmd = [self.okx_bin, "--json"] + args
        env = {**os.environ, "OKX_PROFILE": self.profile}
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8, env=env)
            out = proc.stdout.strip()
            start = next((i for i, ch in enumerate(out) if ch in "[{"), -1)
            if start >= 0:
                parsed = json.loads(out[start:])
                return {"data": parsed} if isinstance(parsed, list) else parsed
        except Exception:
            return None
        return None

    def query_market_snapshot(self, symbol: str) -> Dict[str, Any]:
        res = self._run_okx_readonly(["market", "ticker", symbol])
        if res:
            return {"source": "okx_cli", **res}
        return {"source": "mock", "symbol": symbol, "price": 68000.0, "open_interest_change_pct": 5.1}

    def query_market_filter(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        return {"source": "mock", "criteria": criteria, "symbols": ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]}

    def query_oi_change(self, symbol: str) -> Dict[str, Any]:
        return {"source": "mock", "symbol": symbol, "open_interest_change_pct": 4.2}

    def query_sentiment_snapshot(self, symbol: str) -> Dict[str, Any]:
        return {"source": "mock", "symbol": symbol, "sentiment_score": 0.62, "sentiment_trend": "up"}

    def query_news_risk(self, symbol: str) -> Dict[str, Any]:
        return {"source": "mock", "symbol": symbol, "news_risk": 0.28}

    def query_smartmoney_snapshot(self, symbol: str) -> Dict[str, Any]:
        return {"source": "mock", "symbol": symbol, "weighted_direction": "long", "premium_discount_pct": 0.7}

    def query_smartmoney_trend(self, symbol: str) -> Dict[str, Any]:
        return {"source": "mock", "symbol": symbol, "smart_money_trend": "accumulate"}

    def query_account_snapshot(self) -> Dict[str, Any]:
        res = self._run_okx_readonly(["account", "balance", "--profile", self.profile])
        if res:
            return {"source": "okx_cli", **res}
        return {
            "source": "mock",
            "equity_usdt": 10000,
            "available_usdt": 8000,
            "daily_pnl_pct": -0.4,
            "open_positions_count": 1,
            "total_exposure_pct": 25,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def query_positions(self) -> Dict[str, Any]:
        return {"source": "mock", "positions": []}

    def execute_order_intent(self, intent: OrderIntent, mode: OperatingMode | str) -> Dict[str, Any]:
        run_mode = OperatingMode(mode) if not isinstance(mode, OperatingMode) else mode
        command_preview = f"okx --json swap place --instId {intent.symbol} --side {intent.side} --ordType {intent.entry_type}"

        if self.dry_run or run_mode in {OperatingMode.OBSERVE, OperatingMode.PROPOSE, OperatingMode.DEMO_AUTO}:
            return {"status": "dry_run", "command": command_preview, "executed": False}

        if run_mode == OperatingMode.LIVE_GUARDED and not self.allow_live_execution:
            return {"status": "blocked", "reason": "live_execution_not_allowed", "executed": False}

        return {"status": "blocked", "reason": "v1_intent_only", "executed": False, "command": command_preview}

    def close_position(self, symbol: str, dry_run: bool = True) -> Dict[str, Any]:
        return {"status": "dry_run" if dry_run else "blocked", "symbol": symbol, "executed": False}

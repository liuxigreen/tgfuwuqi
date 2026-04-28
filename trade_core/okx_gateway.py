from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import OperatingMode, OrderIntent


class OkxGateway:
    def __init__(
        self,
        backend: str = "mock",
        profile: str = "demo",
        dry_run: bool = True,
        allow_live: bool = False,
        allow_trade_execution: bool = False,
        command_timeout_seconds: int = 20,
    ):
        self.backend = backend
        self.profile = profile
        self.dry_run = dry_run
        self.allow_live = allow_live
        self.allow_trade_execution = allow_trade_execution
        self.command_timeout_seconds = command_timeout_seconds
        self.okx_bin = shutil.which("okx")

    def command_builder(self, category: str, action: str, *args: str) -> List[str]:
        return [category, action, *args]

    def _run_cli(self, args: List[str]) -> Dict[str, Any]:
        if not self.okx_bin:
            return {"ok": False, "error": "okx_cli_not_found", "args": args}
        cmd = [self.okx_bin, "--json"] + args
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.command_timeout_seconds, env={**os.environ, "OKX_PROFILE": self.profile})
            out = proc.stdout.strip()
            parsed: Any = None
            start = next((i for i, ch in enumerate(out) if ch in "[{"), -1)
            if start >= 0:
                try:
                    parsed = json.loads(out[start:])
                except json.JSONDecodeError:
                    parsed = None
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": out,
                "stderr": proc.stderr.strip(),
                "data": parsed,
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout", "args": args}

    def okx_check(self) -> Dict[str, Any]:
        if self.backend == "mcp":
            return {"backend": "mcp", "status": "todo", "note": "MCP backend reserved"}
        if not self.okx_bin:
            return {"backend": self.backend, "okx_cli": False, "error": "okx_cli_not_found"}
        res = self._run_cli(["--help"])
        return {"backend": self.backend, "okx_cli": True, "help_excerpt": (res.get("stdout", "")[:300]), "profile": self.profile}

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        if self.backend != "cli":
            return {"source": "mock", "symbol": symbol, "price": 68000.0}
        return self._run_cli(self.command_builder("market", "ticker", symbol))

    def get_candles(self, symbol: str, bar: str = "1H", limit: int = 100) -> Dict[str, Any]:
        if self.backend != "cli":
            return {"source": "mock", "symbol": symbol, "bar": bar, "limit": limit, "candles": []}
        return self._run_cli(self.command_builder("market", "candles", symbol, "--bar", bar, "--limit", str(limit)))

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        if self.backend != "cli":
            return {"source": "mock", "symbol": symbol, "funding_rate": 0.0002}
        return self._run_cli(self.command_builder("market", "funding-rate", symbol))

    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        if self.backend != "cli":
            return {"source": "mock", "symbol": symbol, "open_interest": 12345}
        return self._run_cli(self.command_builder("market", "open-interest", symbol))

    def market_filter(self, **criteria: Any) -> Dict[str, Any]:
        return {"source": "mock", "criteria": criteria, "symbols": ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]}

    def get_balance(self) -> Dict[str, Any]:
        if self.backend != "cli":
            return {"source": "mock", "balance": [{"ccy": "USDT", "eq": "10000"}]}
        return self._run_cli(self.command_builder("account", "balance"))

    def get_positions(self) -> Dict[str, Any]:
        if self.backend != "cli":
            return {"source": "mock", "positions": []}
        return self._run_cli(self.command_builder("account", "positions"))

    def get_account_snapshot(self) -> Dict[str, Any]:
        bal = self.get_balance()
        pos = self.get_positions()
        return {
            "source": "mock" if self.backend != "cli" else "cli",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "balance": bal,
            "positions": pos,
        }

    def get_coin_sentiment(self, symbol: str) -> Dict[str, Any]:
        return {"source": "mock", "symbol": symbol, "adapter_status": "mock_only"}

    def get_news_latest(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        return {"source": "mock", "symbol": symbol, "adapter_status": "mock_only", "items": []}

    def get_smartmoney_overview(self, symbol: str) -> Dict[str, Any]:
        return {"source": "mock", "symbol": symbol, "adapter_status": "mock_only"}

    def get_smartmoney_signal_history(self, symbol: str) -> Dict[str, Any]:
        return {"source": "mock", "symbol": symbol, "adapter_status": "mock_only", "history": []}

    def get_trader_leaderboard(self) -> Dict[str, Any]:
        return {"source": "mock", "adapter_status": "mock_only", "leaders": []}

    def execute_order_intent(self, intent: OrderIntent, mode: OperatingMode | str) -> Dict[str, Any]:
        run_mode = OperatingMode(mode) if not isinstance(mode, OperatingMode) else mode
        if self.profile != "demo":
            return {"status": "blocked", "reason": "live_profile_blocked", "executed": False}
        if not self.allow_live and self.profile == "live":
            return {"status": "blocked", "reason": "allow_live_false", "executed": False}
        if self.dry_run or intent.dry_run:
            return {"status": "dry_run", "executed": False, "intent": {"symbol": intent.symbol, "side": intent.side, "size": intent.size}}
        if run_mode != OperatingMode.DEMO_AUTO:
            return {"status": "blocked", "reason": "mode_not_demo_auto", "executed": False}
        if self.backend != "cli" or not self.allow_trade_execution:
            return {"status": "blocked", "reason": "trade_execution_not_allowed", "executed": False}
        if intent.side not in {"buy", "sell"} or intent.size <= 0:
            return {"status": "blocked", "reason": "invalid_intent", "executed": False}

        args = self.command_builder(intent.market_type, "place", "--instId", intent.symbol, "--side", intent.side, "--ordType", intent.entry_type, "--sz", str(intent.size))
        res = self._run_cli(args)
        return {"status": "executed" if res.get("ok") else "failed", "executed": bool(res.get("ok")), "result": res}

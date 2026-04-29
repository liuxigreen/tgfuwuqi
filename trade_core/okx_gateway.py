from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import OperatingMode, OrderIntent


class OkxGateway:
    def __init__(self, backend: str = "mock", profile: str = "demo", dry_run: bool = True, allow_live: bool = False, allow_trade_execution: bool = False, command_timeout_seconds: int = 20):
        self.backend = backend
        self.profile = profile
        self.dry_run = dry_run
        self.allow_live = allow_live
        self.allow_trade_execution = allow_trade_execution
        self.command_timeout_seconds = command_timeout_seconds
        self.okx_bin = shutil.which("okx")

    def command_builder(self, category: str, action: str, *args: str) -> List[str]:
        return [category, action, *args]

    def _run_cli(self, args: List[str], use_json: bool = True) -> Dict[str, Any]:
        if not self.okx_bin:
            return {"ok": False, "error": "okx_cli_not_found", "args": args}
        cmd = [self.okx_bin] + (["--json"] if use_json else []) + args
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.command_timeout_seconds)
            out = proc.stdout.strip()
            parsed: Any = None
            if use_json:
                start = next((i for i, ch in enumerate(out) if ch in "[{"), -1)
                if start >= 0:
                    try:
                        parsed = json.loads(out[start:])
                    except Exception:
                        parsed = None
            return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": out, "stderr": proc.stderr.strip(), "data": parsed}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout", "args": args}

    def okx_check(self) -> Dict[str, Any]:
        if self.backend == "mcp":
            return {"backend": "mcp", "status": "todo", "warning": "mcp_backend_reserved"}
        if not self.okx_bin:
            return {"backend": self.backend, "okx_cli": False, "error": "okx_cli_not_found"}
        help_res = self._run_cli(["--help"], use_json=False)
        return {"backend": self.backend, "okx_cli": True, "help_excerpt": help_res.get("stdout", "")[:300], "profile": self.profile}

    def _mock(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {**payload, "source": "mock", "is_mock": True}

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        if self.backend != "cli":
            return self._mock({"symbol": symbol, "price": 68000.0})
        return self._run_cli(self.command_builder("market", "ticker", symbol))

    def get_candles(self, symbol: str, bar: str = "1H", limit: int = 100) -> Dict[str, Any]:
        if self.backend != "cli":
            return self._mock({"symbol": symbol, "bar": bar, "limit": limit, "candles": []})
        return self._run_cli(self.command_builder("market", "candles", symbol, "--bar", bar, "--limit", str(limit)))

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        if self.backend != "cli":
            return self._mock({"symbol": symbol, "funding_rate": 0.0002})
        return self._run_cli(self.command_builder("market", "funding-rate", symbol))

    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        if self.backend != "cli":
            return self._mock({"symbol": symbol, "open_interest": 12345})
        return self._run_cli(self.command_builder("market", "open-interest", symbol))

    def get_market_snapshot(self, symbol: str) -> Dict[str, Any]:
        return {"ticker": self.get_ticker(symbol), "funding": self.get_funding_rate(symbol), "open_interest": self.get_open_interest(symbol)}

    def get_balance(self) -> Dict[str, Any]:
        if self.backend != "cli":
            return self._mock({"balance": [{"ccy": "USDT", "eq": "10000"}]})
        return self._run_cli(self.command_builder("account", "balance"))

    def get_positions(self) -> Dict[str, Any]:
        if self.backend != "cli":
            return self._mock({"positions": []})
        return self._run_cli(self.command_builder("account", "positions"))

    def get_account_snapshot(self) -> Dict[str, Any]:
        bal = self.get_balance(); pos = self.get_positions()
        return {"available_equity": None, "total_equity": None, "open_positions_count": len(pos.get("positions", [])) if isinstance(pos, dict) else 0, "total_exposure_pct": None, "daily_pnl_pct": None, "timestamp": datetime.now(timezone.utc).isoformat(), "source": "mock" if self.backend != "cli" else "cli", "is_mock": self.backend != "cli", "warning": "daily_pnl_unavailable", "balance": bal, "positions": pos}

    def get_coin_sentiment(self, symbol: str) -> Dict[str, Any]:
        if self.backend == "cli":
            return {"error": "adapter_unavailable", "adapter": "sentiment", "symbol": symbol}
        return self._mock({"symbol": symbol, "sentiment_score": 0.55, "sentiment_trend": "neutral", "confidence": 0.4, "timestamp": datetime.now(timezone.utc).isoformat(), "source": "mock_sentiment"})

    def get_news_latest(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        if self.backend == "cli":
            return {"error": "adapter_unavailable", "adapter": "news", "symbol": symbol}
        return self._mock({"symbol": symbol, "items": []})

    def get_smartmoney_overview(self, symbol: str) -> Dict[str, Any]:
        if self.backend == "cli":
            return {"error": "adapter_unavailable", "adapter": "smartmoney", "symbol": symbol}
        return self._mock({"symbol": symbol, "long_short_ratio": 1.1, "capital_weighted_direction": "long", "average_win_rate": 0.6, "smart_trader_count": 12, "average_entry_price": 67000, "confidence": 0.5, "trend": "flat", "timestamp": datetime.now(timezone.utc).isoformat(), "source": "mock_smartmoney"})

    def get_smartmoney_signal_history(self, symbol: str) -> Dict[str, Any]:
        return self._mock({"symbol": symbol, "history": []}) if self.backend != "cli" else {"error": "adapter_unavailable", "adapter": "smartmoney_history", "symbol": symbol}

    def get_trader_leaderboard(self, filters: Optional[dict] = None) -> Dict[str, Any]:
        return self._mock({"filters": filters or {}, "leaders": []}) if self.backend != "cli" else {"error": "adapter_unavailable", "adapter": "leaderboard"}

    def execute_order_intent(self, intent: OrderIntent, mode: OperatingMode | str, risk_result: Optional[Dict[str, Any]] = None, demo_execute: bool = False) -> Dict[str, Any]:
        run_mode = OperatingMode(mode) if not isinstance(mode, OperatingMode) else mode
        command_preview = f"okx {intent.market_type} place --instId {intent.symbol} --side {intent.side} --ordType {intent.entry_type} --sz {intent.size}"
        if self.profile == "live" or (not self.allow_live and self.profile != "demo"):
            return {"executed": False, "dry_run": True, "blocked": True, "backend": self.backend, "profile": self.profile, "command_preview": command_preview, "stdout_summary": "", "stderr_summary": "", "returncode": None, "error_code": "live_profile_blocked", "timestamp": datetime.now(timezone.utc).isoformat()}

        allow_real_demo = all([
            self.backend == "cli",
            self.profile == "demo",
            self.allow_trade_execution,
            not self.allow_live,
            run_mode == OperatingMode.DEMO_AUTO,
            demo_execute,
            not intent.dry_run,
            bool(risk_result is None or risk_result.get("passed", True)),
        ])

        if self.dry_run or not allow_real_demo:
            return {"executed": False, "dry_run": True, "blocked": False if self.profile == "demo" else True, "backend": self.backend, "profile": self.profile, "command_preview": command_preview, "stdout_summary": "dry-run", "stderr_summary": "", "returncode": None, "error_code": None if self.profile == "demo" else "profile_blocked", "timestamp": datetime.now(timezone.utc).isoformat()}

        res = self._run_cli(self.command_builder(intent.market_type, "place", "--instId", intent.symbol, "--side", intent.side, "--ordType", intent.entry_type, "--sz", str(intent.size)))
        return {"executed": bool(res.get("ok")), "dry_run": False, "blocked": not bool(res.get("ok")), "backend": self.backend, "profile": self.profile, "command_preview": command_preview, "stdout_summary": (res.get("stdout") or "")[:240], "stderr_summary": (res.get("stderr") or "")[:240], "returncode": res.get("returncode"), "error_code": None if res.get("ok") else "cli_execution_failed", "timestamp": datetime.now(timezone.utc).isoformat()}

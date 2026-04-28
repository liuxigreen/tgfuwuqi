from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from typing import Any, Dict

from .cache import TTLCache


@dataclass
class FastContext:
    signal: Dict[str, Any]
    market_snapshot: Dict[str, Any] | None
    oi_snapshot: Dict[str, Any] | None
    funding_snapshot: Dict[str, Any] | None
    account_snapshot: Dict[str, Any] | None
    sentiment_snapshot: Dict[str, Any] | None
    smartmoney_snapshot: Dict[str, Any] | None
    adapter_status: Dict[str, str]
    missing_inputs: list
    warnings: list
    latency_ms: float
    degraded_mode: bool
    cache_status: Dict[str, Any]


def enrich_fast_context(signal, mode, gateway, cache: TTLCache, latency_budget: Dict[str, Any]) -> FastContext:
    adapter_status = {}
    missing = []
    warnings = []
    cache_status = {}
    symbol = signal["symbol"] if isinstance(signal, dict) else signal.symbol

    tasks = {
        "market": lambda: gateway.get_ticker(symbol),
        "oi": lambda: gateway.get_open_interest(symbol),
        "funding": lambda: gateway.get_funding_rate(symbol),
        "account": gateway.get_account_snapshot,
        "sentiment": lambda: gateway.get_coin_sentiment(symbol),
        "smartmoney": lambda: gateway.get_smartmoney_overview(symbol),
    }
    results = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        fs = {name: ex.submit(fn) for name, fn in tasks.items()}
        for name, future in fs.items():
            try:
                timeout = latency_budget.get(f"{name}_timeout_ms", latency_budget.get("adapter_timeout_ms", 900)) / 1000
                res = future.result(timeout=timeout)
                if isinstance(res, dict) and res.get("error"):
                    adapter_status[name] = "unavailable"
                    missing.append(name)
                else:
                    adapter_status[name] = "ok"
                results[name] = res
            except TimeoutError:
                adapter_status[name] = "timeout"; missing.append(name); results[name] = None
            except Exception:
                adapter_status[name] = "error"; missing.append(name); results[name] = None

    if mode == "demo_auto" and ("account" in missing or "market" in missing):
        warnings.append("critical_adapter_missing")

    return FastContext(signal=signal, market_snapshot=results.get("market"), oi_snapshot=results.get("oi"), funding_snapshot=results.get("funding"), account_snapshot=results.get("account"), sentiment_snapshot=results.get("sentiment"), smartmoney_snapshot=results.get("smartmoney"), adapter_status=adapter_status, missing_inputs=missing, warnings=warnings, latency_ms=0.0, degraded_mode=bool(missing), cache_status=cache_status)

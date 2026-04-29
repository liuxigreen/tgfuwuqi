from __future__ import annotations

import time
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
    start=time.perf_counter()
    adapter_status = {}
    missing = []
    warnings = []
    cache_status = {}
    symbol = signal["symbol"] if isinstance(signal, dict) else signal.symbol

    defs = {
        "market": (f"ticker:{symbol}", int(latency_budget.get('ttl_ticker', 1)), lambda: gateway.get_ticker(symbol)),
        "oi": (f"oi:{symbol}", int(latency_budget.get('ttl_open_interest', 30)), lambda: gateway.get_open_interest(symbol)),
        "funding": (f"funding:{symbol}", int(latency_budget.get('ttl_funding', 30)), lambda: gateway.get_funding_rate(symbol)),
        "account": ("account", int(latency_budget.get('ttl_account', 10)), gateway.get_account_snapshot),
        "sentiment": (f"sent:{symbol}", int(latency_budget.get('ttl_sentiment', 60)), lambda: gateway.get_coin_sentiment(symbol)),
        "smartmoney": (f"sm:{symbol}", int(latency_budget.get('ttl_smartmoney', 60)), lambda: gateway.get_smartmoney_overview(symbol)),
    }

    results={}
    pending={}
    with ThreadPoolExecutor(max_workers=6) as ex:
        for name,(ckey,ttl,fn) in defs.items():
            val,fresh,stale=cache.get(ckey)
            if fresh:
                results[name]=val; adapter_status[name]='ok'; cache_status[name]='hit'
            else:
                cache_status[name]='stale_cache' if stale else 'miss'
                pending[name]=(ckey,ttl,ex.submit(fn))

        for name,(ckey,ttl,future) in pending.items():
            try:
                timeout = latency_budget.get(f"{name}_timeout_ms", latency_budget.get("adapter_timeout_ms", 900)) / 1000
                res = future.result(timeout=timeout)
                if isinstance(res, dict) and res.get('error'):
                    if cache_status[name]=='stale_cache':
                        val,_,_=cache.get(ckey); results[name]=val; adapter_status[name]='stale_cache'; warnings.append(f'{name}_using_stale_cache')
                    else:
                        results[name]=None; adapter_status[name]='unavailable'; missing.append(name)
                else:
                    results[name]=res; adapter_status[name]='ok'; cache.set(ckey,res,ttl)
            except TimeoutError:
                if cache_status[name]=='stale_cache':
                    val,_,_=cache.get(ckey); results[name]=val; adapter_status[name]='stale_cache'; warnings.append(f'{name}_timeout_using_stale_cache')
                else:
                    results[name]=None; adapter_status[name]='timeout'; missing.append(name)
            except Exception:
                results[name]=None; adapter_status[name]='error'; missing.append(name)

    if mode == "demo_auto" and ("account" in missing or "market" in missing):
        warnings.append("critical_adapter_missing")
    latency_ms=(time.perf_counter()-start)*1000
    return FastContext(signal=signal, market_snapshot=results.get('market'), oi_snapshot=results.get('oi'), funding_snapshot=results.get('funding'), account_snapshot=results.get('account'), sentiment_snapshot=results.get('sentiment'), smartmoney_snapshot=results.get('smartmoney'), adapter_status=adapter_status, missing_inputs=missing, warnings=warnings, latency_ms=round(latency_ms,2), degraded_mode=bool(missing or any(v=='stale_cache' for v in adapter_status.values())), cache_status=cache_status)

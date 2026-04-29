from __future__ import annotations

import json
from typing import Any, Dict

from .cache import TTLCache
from .config import load_config
from .daily_limits import check_daily_limits
from .enrichment import enrich_fast_context
from .latency import LatencyTracker
from .lifecycle import run_demo_execution_pipeline, run_pretrade_pipeline
from .learning_loop.retriever import retrieve_similar_experiences
from .journal import write_journal_event

_GLOBAL_CACHE = TTLCache()


def run_fast_signal_pipeline(signal_or_sample: Dict[str, Any], mode: str = 'propose', demo_execute: bool = False, cache: TTLCache | None = None) -> Dict[str, Any]:
    cfg = load_config(); lat = cfg['latency']; tracker = LatencyTracker();
    tracker.mark('normalize')
    sample = signal_or_sample if 'radar_signal' in signal_or_sample else json.loads(json.dumps(signal_or_sample))

    from .okx_gateway import OkxGateway
    gw = OkxGateway(backend=cfg['okx_gateway'].get('backend','mock'), profile=cfg['okx_gateway'].get('profile','demo'), dry_run=not demo_execute, allow_live=cfg['okx_gateway'].get('allow_live',False), allow_trade_execution=cfg['okx_gateway'].get('allow_trade_execution',False), command_timeout_seconds=int(cfg['okx_gateway'].get('command_timeout_seconds',20)))
    fast_ctx = enrich_fast_context(sample['radar_signal'], mode, gw, cache or _GLOBAL_CACHE, {**lat, **cfg.get('cache', {})})
    tracker.mark('enrich')

    ll_cfg = cfg.get("learning_loop", {}).get("experience_retrieval", {})
    similar = {"used": False, "experiences": [], "experience_adjustments": {"score_adjustment": 0}}
    if ll_cfg.get("enabled", True) and ll_cfg.get("allow_in_fast_path", True):
        similar = retrieve_similar_experiences({"symbol": sample['radar_signal']['symbol'], "market_type": sample['radar_signal'].get('market_type'), "direction": sample['radar_signal'].get('direction'), "tags": list((sample['radar_signal'].get('features') or {}).keys())}, top_k=int(ll_cfg.get('top_k',5)), max_latency_ms=int(ll_cfg.get('max_latency_ms',200)), min_similarity=float(ll_cfg.get('min_similarity',0.55)))

    # merge fast context back into sample (full snapshots, no fabricated defaults)
    if fast_ctx.market_snapshot is not None:
        sample['market_snapshot'] = dict(fast_ctx.market_snapshot)
    if fast_ctx.oi_snapshot is not None:
        sample['oi_snapshot'] = dict(fast_ctx.oi_snapshot)
    if fast_ctx.funding_snapshot is not None:
        sample['funding_snapshot'] = dict(fast_ctx.funding_snapshot)
    if fast_ctx.account_snapshot is not None:
        sample['account_snapshot'] = dict(fast_ctx.account_snapshot)
    if fast_ctx.sentiment_snapshot is not None:
        sample['sentiment_snapshot'] = dict(fast_ctx.sentiment_snapshot)
    if fast_ctx.smartmoney_snapshot is not None:
        sample['smartmoney_snapshot'] = dict(fast_ctx.smartmoney_snapshot)

    # execution gates from fast context
    critical_missing = ('market' in fast_ctx.missing_inputs) or ('account' in fast_ctx.missing_inputs)
    optional_missing = ('sentiment' in fast_ctx.missing_inputs) or ('smartmoney' in fast_ctx.missing_inputs)

    if mode == 'demo_auto' and critical_missing:
        demo_execute = False

    if mode == 'demo_auto' and optional_missing:
        if ('sentiment' in fast_ctx.missing_inputs and not lat.get('allow_missing_sentiment_in_demo_auto', False)) or ('smartmoney' in fast_ctx.missing_inputs and not lat.get('allow_missing_smartmoney_in_demo_auto', False)):
            demo_execute = False

    result = run_demo_execution_pipeline(sample, demo_execute=demo_execute, backend=cfg['okx_gateway'].get('backend','mock'), profile=cfg['okx_gateway'].get('profile','demo')) if mode == 'demo_auto' else run_pretrade_pipeline(sample, mode=mode)
    tracker.mark('decision')

    limits = check_daily_limits(result['symbol'], result['action'], cfg)
    result['daily_limits_status'] = limits
    if not limits['passed']:
        result['execution_allowed'] = False
        result['execution_blocked_reason'] = limits['blocked_reasons']
    total = tracker.summary()['total_ms']
    latency_summary = tracker.summary(); latency_summary['enrich_ms'] = fast_ctx.latency_ms
    result['latency_summary'] = latency_summary
    result['latency_ms'] = total
    result['fast_path'] = True
    result['degraded_mode'] = fast_ctx.degraded_mode
    result['adapter_status'] = fast_ctx.adapter_status
    result['adapter_is_mock'] = {k: bool((sample.get(f'{k}_snapshot') or {}).get('is_mock')) for k in ['market','oi','funding','account','sentiment','smartmoney']}
    result['cache_status'] = fast_ctx.cache_status
    result['missing_inputs'] = fast_ctx.missing_inputs
    result['nuwa_mode'] = 'fast'
    result['experience_retrieval_used'] = bool(similar.get('used'))
    result['similar_experience_count'] = len(similar.get('experiences', []))
    result['similar_experiences'] = similar.get('experiences', [])
    result['experience_adjustments'] = similar.get('experience_adjustments', {})
    result['fast_context_used'] = True
    result['execution_allowed'] = result.get('execution_allowed', not critical_missing)
    if mode == 'demo_auto' and critical_missing:
        result['action'] = 'blocked'
    result['execution_blocked_reason'] = result.get('execution_blocked_reason', [])

    # stale market/account must not execute
    if mode == 'demo_auto' and (fast_ctx.adapter_status.get('market') == 'stale_cache' or fast_ctx.adapter_status.get('account') == 'stale_cache'):
        result['execution_allowed'] = False
        result['execution_blocked_reason'] = sorted(set(result.get('execution_blocked_reason', []) + ['stale_cache_block_execution']))

    if total > float(lat.get('fast_path_target_total_ms', 4000)):
        result['reason_codes'] = sorted(set(result.get('reason_codes', []) + ['latency_budget_exceeded']))
        if mode == 'demo_auto':
            result['execution_allowed'] = False
            result['execution_blocked_reason'] = sorted(set(result.get('execution_blocked_reason', []) + ['latency_budget_exceeded']))
    if total > float(lat.get('fast_path_hard_timeout_ms', 5000)) and mode == 'demo_auto':
        result['action'] = 'propose'
        result['execution_allowed'] = False
        result['execution_blocked_reason'] = sorted(set(result.get('execution_blocked_reason', []) + ['hard_timeout']))
    return result

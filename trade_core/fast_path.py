from __future__ import annotations

import json
from typing import Any, Dict

from .cache import TTLCache
from .config import load_config
from .daily_limits import check_daily_limits
from .enrichment import enrich_fast_context
from .latency import LatencyTracker
from .lifecycle import run_demo_execution_pipeline


def run_fast_signal_pipeline(signal_or_sample: Dict[str, Any], mode: str = 'propose', demo_execute: bool = False) -> Dict[str, Any]:
    cfg = load_config(); lat = cfg['latency']; tracker = LatencyTracker();
    tracker.mark('normalize')
    sample = signal_or_sample if 'radar_signal' in signal_or_sample else json.loads(json.dumps(signal_or_sample))

    from .okx_gateway import OkxGateway
    gw = OkxGateway(backend=cfg['okx_gateway'].get('backend','mock'), profile=cfg['okx_gateway'].get('profile','demo'), dry_run=not demo_execute, allow_live=cfg['okx_gateway'].get('allow_live',False), allow_trade_execution=cfg['okx_gateway'].get('allow_trade_execution',False), command_timeout_seconds=int(cfg['okx_gateway'].get('command_timeout_seconds',20)))
    fast_ctx = enrich_fast_context(sample['radar_signal'], mode, gw, TTLCache(), lat)
    tracker.mark('enrich')

    result = run_demo_execution_pipeline(sample, demo_execute=demo_execute, backend=cfg['okx_gateway'].get('backend','mock'), profile=cfg['okx_gateway'].get('profile','demo')) if mode == 'demo_auto' else __import__('trade_core.lifecycle', fromlist=['run_pretrade_pipeline']).run_pretrade_pipeline(sample, mode=mode)
    tracker.mark('decision')

    limits = check_daily_limits(result['symbol'], result['action'], cfg)
    result['daily_limits_status'] = limits
    if not limits['passed']:
        result['execution_allowed'] = False
        result['execution_blocked_reason'] = limits['blocked_reasons']
    total = tracker.summary()['total_ms']
    latency_summary = tracker.summary(); latency_summary['enrich_ms'] = latency_summary.get('enrich_ms',0)
    result['latency_summary'] = latency_summary
    result['latency_ms'] = total
    result['fast_path'] = True
    result['degraded_mode'] = fast_ctx.degraded_mode
    result['adapter_status'] = fast_ctx.adapter_status
    result['cache_status'] = fast_ctx.cache_status
    result['nuwa_mode'] = 'fast'
    result['execution_allowed'] = result.get('execution_allowed', True)
    result['execution_blocked_reason'] = result.get('execution_blocked_reason', [])

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

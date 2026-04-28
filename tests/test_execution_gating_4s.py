import json
from trade_core.fast_path import run_fast_signal_pipeline


def test_demo_auto_over_budget_blocks_execution():
    sample=json.loads(open('examples/fast_signal_long_case.json','r',encoding='utf-8').read())
    out=run_fast_signal_pipeline(sample,mode='demo_auto',demo_execute=True)
    if out['latency_ms']>4000:
        assert out['execution_allowed'] is False

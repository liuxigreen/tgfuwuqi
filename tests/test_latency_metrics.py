import json
from trade_core.fast_path import run_fast_signal_pipeline
from trade_core.self_evolution import daily_review


def test_latency_in_pipeline_and_review(tmp_path):
    sample=json.loads(open('examples/fast_signal_long_case.json','r',encoding='utf-8').read())
    out=run_fast_signal_pipeline(sample,mode='propose')
    assert 'latency_summary' in out

import json
from trade_core.fast_path import run_fast_signal_pipeline


def test_fast_signal_pipeline_basic():
    sample=json.loads(open('examples/fast_signal_long_case.json','r',encoding='utf-8').read())
    out=run_fast_signal_pipeline(sample,mode='propose')
    assert 'latency_summary' in out and out['fast_path'] is True


def test_timeout_degrades_or_blocks():
    sample=json.loads(open('examples/fast_signal_timeout_case.json','r',encoding='utf-8').read())
    out=run_fast_signal_pipeline(sample,mode='demo_auto')
    assert out['action'] in {'propose','blocked','observe'}

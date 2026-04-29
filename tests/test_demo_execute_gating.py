import json
from trade_core.lifecycle import run_demo_execution_pipeline


def load(path='examples/full_case.json'):
    return json.loads(open(path,'r',encoding='utf-8').read())


def test_default_dry_run():
    out=run_demo_execution_pipeline(load(), demo_execute=False, backend='cli', profile='demo')
    assert out['execution_result']['dry_run'] is True


def test_demo_execute_but_not_allowed_blocked_or_dry():
    out=run_demo_execution_pipeline(load(), demo_execute=True, backend='cli', profile='demo')
    assert out['execution_result']['executed'] is False


def test_profile_live_blocked():
    out=run_demo_execution_pipeline(load(), demo_execute=True, backend='cli', profile='live')
    assert out['execution_result']['blocked'] is True


def test_backend_mock_not_real_exec():
    out=run_demo_execution_pipeline(load(), demo_execute=True, backend='mock', profile='demo')
    assert out['execution_result']['executed'] is False

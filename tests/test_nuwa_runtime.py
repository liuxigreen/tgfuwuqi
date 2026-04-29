import json
from trade_core.config import load_config
from trade_core.lifecycle import run_pretrade_pipeline
from trade_core.nuwa_runtime import load_registry, run_nuwa_evaluation, run_shadow_nuwa_evaluations


def test_registry_loads():
    r=load_registry(load_config())
    assert r['default_nuwa_version']


def test_missing_skill_warning():
    r=load_registry({'nuwa_runtime':{'default_nuwa_version':'x','min_confidence_for_demo_auto':0.65,'versions':{'x':{'skill_path':'nope','enabled':True,'mode':'mock_structured'}}}})
    assert r['warnings']


def test_block_trade_blocks(tmp_path):
    sample=json.loads(open('examples/nuwa_block_trade_case.json','r',encoding='utf-8').read())
    out=run_pretrade_pipeline(sample,journal_dir=str(tmp_path))
    assert out['action']=='blocked'


def test_low_confidence_blocks_demo_auto(tmp_path):
    sample=json.loads(open('examples/low_confidence_nuwa_case.json','r',encoding='utf-8').read())
    out=run_pretrade_pipeline(sample,mode='demo_auto',journal_dir=str(tmp_path))
    assert out['action'] in {'blocked','observe'}


def test_mock_reason_codes_and_shadow():
    ev=run_nuwa_evaluation({},'nuwa_default_v1')
    assert 'nuwa_mock_eval' in ev['reason_codes']
    sh=run_shadow_nuwa_evaluations({},['a','b'])
    assert len(sh)==2

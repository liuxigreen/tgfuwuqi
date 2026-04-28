import json
from trade_core.lifecycle import run_pretrade_pipeline


def test_decision_has_score_breakdown(tmp_path):
    sample=json.loads(open('examples/full_case.json','r',encoding='utf-8').read())
    out=run_pretrade_pipeline(sample,journal_dir=str(tmp_path))
    assert 'score_breakdown' in out
    assert 'market_score' in out['score_breakdown']


def test_journal_has_score_breakdown(tmp_path):
    sample=json.loads(open('examples/full_case.json','r',encoding='utf-8').read())
    out=run_pretrade_pipeline(sample,journal_dir=str(tmp_path))
    text=open(out['journal_path'],'r',encoding='utf-8').read()
    assert 'score_breakdown' in text


def test_missing_optional_inputs_no_crash(tmp_path):
    sample=json.loads(open('examples/unknown_direction_case.json','r',encoding='utf-8').read())
    out=run_pretrade_pipeline(sample,journal_dir=str(tmp_path))
    assert 'warnings' in out

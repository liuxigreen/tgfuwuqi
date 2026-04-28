import json
from trade_core.lifecycle import run_pretrade_pipeline
from trade_core.journal import review_journal
from trade_core.replay import replay_journal
from trade_core.reporting import build_daily_report


def test_replay_review_report(tmp_path):
    sample=json.loads(open('examples/full_case.json','r',encoding='utf-8').read())
    out=run_pretrade_pipeline(sample,journal_dir=str(tmp_path))
    rp=replay_journal(out['journal_path'])
    rv=review_journal(out['journal_path'])
    report=build_daily_report(out['journal_path'])
    assert rp['ok']
    assert 'total_decisions' in rv
    assert report.markdown
    assert 'secret' not in report.markdown

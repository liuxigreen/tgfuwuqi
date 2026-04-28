from trade_core.nuwa_runtime.fast_evaluator import run_fast_nuwa


def test_fast_nuwa_structured():
    out=run_fast_nuwa({'nuwa_eval':{'signal_quality':70,'continuation_probability':0.6,'manipulation_risk':0.4,'preferred_action':'observe','confidence':0.6,'block_trade':False}})
    assert 'signal_quality' in out


def test_fast_nuwa_timeout_default():
    out=run_fast_nuwa({'simulate_nuwa_timeout':True})
    assert 'nuwa_fast_timeout' in out['reason_codes']

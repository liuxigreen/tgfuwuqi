import json
from trade_core.lifecycle import run_position_management


def load():
    return json.loads(open('examples/position_case.json','r',encoding='utf-8').read())


def test_context_eaten():
    sample=load()
    sample['nuwa_eval']={'version':'v','market_regime':'trend','signal_archetype':'x','signal_quality':0.6,'continuation_probability':0.5,'manipulation_risk':0.2,'preferred_action':'propose','block_trade':False,'confidence':0.7,'thesis_status':'weakening'}
    sample['sentiment_snapshot']={'symbol':'BTC-USDT-SWAP','sentiment_score':0.2,'sentiment_trend':'down','abnormal_sentiment_shift':False,'news_risk':0.1,'timestamp':'2026-04-28T15:30:00Z'}
    sample['smartmoney_snapshot']={'symbol':'BTC-USDT-SWAP','consensus_direction':'short','weighted_direction':'short','avg_win_rate':0.6,'long_short_ratio':0.8,'smart_money_trend':'reversal','entry_vwap':68000,'current_price':69000,'premium_discount_pct':0.2,'timestamp':'2026-04-28T15:30:00Z'}
    out=run_position_management(sample)
    assert 'evaluation' in out

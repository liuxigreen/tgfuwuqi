from trade_core.journal import write_journal_event


def test_recursive_redaction(tmp_path):
    payload={'a':{'token':'abc','nested':[{'secret':'x'}]},'price':123}
    p=write_journal_event('decision','p1','BTC-USDT',payload,base_dir=str(tmp_path))
    txt=open(p,'r',encoding='utf-8').read()
    assert 'abc' not in txt and '"price": 123' in txt

from trade_core.okx_gateway import OkxGateway
from trade_core.scout import run_scout


def test_mock_flag_true():
    out=run_scout(['BTC-USDT-SWAP'],'propose',OkxGateway(backend='mock'))
    assert out['is_mock'] is True


def test_demo_auto_mock_not_execute():
    out=run_scout(['BTC-USDT-SWAP'],'demo_auto',OkxGateway(backend='mock'))
    assert out['candidates'][0]['suggested_action']=='observe'


def test_missing_adapter_warning():
    out=run_scout(['BTC-USDT-SWAP'],'propose',OkxGateway(backend='cli'))
    assert 'warnings' in out

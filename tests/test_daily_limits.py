from trade_core.config import load_config
from trade_core.daily_limits import check_daily_limits, record_trade


def test_max_trades_block(tmp_path):
    cfg=load_config(); p=str(tmp_path/'state.json')
    for _ in range(8):
        record_trade('BTC-USDT-SWAP',1,p)
    out=check_daily_limits('BTC-USDT-SWAP','open_long',cfg,p)
    assert out['passed'] is False

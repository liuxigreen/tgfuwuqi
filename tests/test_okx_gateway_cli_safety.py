import inspect
from trade_core.okx_gateway import OkxGateway


def test_cli_missing_structured_error():
    gw=OkxGateway(backend='cli')
    if not gw.okx_bin:
        assert gw.get_ticker('BTC-USDT').get('error')=='okx_cli_not_found'


def test_okx_check_safe():
    gw=OkxGateway(backend='cli')
    out=gw.okx_check()
    assert 'backend' in out


def test_shell_false_by_implementation():
    src=inspect.getsource(OkxGateway._run_cli)
    assert 'shell=True' not in src


def test_live_blocked():
    gw=OkxGateway(backend='cli',profile='live',dry_run=False,allow_live=False,allow_trade_execution=True)
    from trade_core.models import OrderIntent
    out=gw.execute_order_intent(OrderIntent('BTC-USDT','buy','spot','percent_equity',1.0,'limit',0.02,0.05,True,True,False,['x'],{},'v','d'),'demo_auto',demo_execute=True)
    assert out['blocked'] is True

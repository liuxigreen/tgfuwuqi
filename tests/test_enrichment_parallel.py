from trade_core.cache import TTLCache
from trade_core.config import load_config
from trade_core.enrichment import enrich_fast_context
from trade_core.okx_gateway import OkxGateway


def test_enrichment_no_crash_with_timeouts():
    cfg=load_config()['latency']
    out=enrich_fast_context({'symbol':'BTC-USDT-SWAP'},'propose',OkxGateway(backend='mock'),TTLCache(),cfg)
    assert out.adapter_status


def test_missing_account_demo_auto_flagged():
    cfg=load_config()['latency']
    out=enrich_fast_context({'symbol':'BTC-USDT-SWAP'},'demo_auto',OkxGateway(backend='cli'),TTLCache(),cfg)
    assert 'account' in out.adapter_status

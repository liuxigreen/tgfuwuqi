import time
from trade_core.cache import TTLCache


def test_cache_hit_and_stale():
    c=TTLCache(); c.set('k',1,1)
    v,fresh,stale=c.get('k')
    assert fresh and not stale
    time.sleep(1.1)
    _,fresh,stale=c.get('k')
    assert stale

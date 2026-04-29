from trade_core.config import load_config
from trade_core.models import Direction, PositionState
from trade_core.position_manager import evaluate_position_exit


def test_exit_rules_loaded():
    cfg=load_config()
    assert 'exit_rules' in cfg and 'first_tp_pct' in cfg['exit_rules']


def test_first_tp_change_affects_result():
    ps=PositionState('1','BTC-USDT-SWAP',Direction.LONG,100,103,0.03,10,[],'x',0.02,0.08)
    out1=evaluate_position_exit(ps,rules={'first_tp_pct':0.03})
    out2=evaluate_position_exit(ps,rules={'first_tp_pct':0.05})
    assert out1.recommended_action!=out2.recommended_action


def test_stop_loss_change_affects_result():
    ps=PositionState('1','BTC-USDT-SWAP',Direction.LONG,100,98,-0.02,10,[],'x',0.02,0.08)
    out1=evaluate_position_exit(ps,rules={'stop_loss_pct':0.02})
    out2=evaluate_position_exit(ps,rules={'stop_loss_pct':0.03})
    assert out1.recommended_action!=out2.recommended_action

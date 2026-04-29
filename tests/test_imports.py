def test_core_imports():
    import trade_core  # noqa: F401
    from trade_core.fast_path import run_fast_signal_pipeline  # noqa: F401
    from trade_core.config import load_config  # noqa: F401
    from trade_core.order_intent import build_order_intent  # noqa: F401
    from trade_core.daily_limits import check_daily_limits  # noqa: F401
    from trade_core.exit_policy import select_exit_policy  # noqa: F401

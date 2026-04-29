# Module Map (Recommended)

## Proposed directory map

```text
trade_core/
  __init__.py
  models.py
  config.py
  signal_bus.py
  fast_path.py
  slow_path.py
  enrichment.py
  decision.py
  scoring.py
  risk.py
  daily_limits.py
  order_intent.py
  position_manager.py
  okx_gateway.py
  journal.py
  replay.py
  reporting.py
  latency.py
  cache.py
  utils.py
  cli.py

  nuwa_runtime/
    __init__.py
    schema.py
    registry.py
    loader.py
    fast_evaluator.py
    deep_evaluator.py
    mock_evaluator.py

  exit_policy/
    __init__.py
    models.py
    templates.py
    selector.py
    evaluator.py
    simulator.py
    optimizer.py
    metrics.py

  learning_loop/
    __init__.py
    snapshot.py
    outcome.py
    reviewer.py
    experience_store.py
    retriever.py
    calibration.py
    feedback.py
    bootstrap.py
    proposals.py

  skill_intelligence/
    __init__.py
    models.py
    registry.py
    classifier.py
    evaluator.py
    recipes.py
    router.py
    metrics.py
    discovery.py
    updater.py

  self_evolution/
    __init__.py
    analyzer.py
    metrics.py
    performance_metrics.py
    guardrails.py
    proposals.py
```

## Ownership by concern
- **Core runtime (fast path):** `fast_path`, `enrichment`, `decision`, `scoring`, `risk`, `daily_limits`, `order_intent`, `exit_policy/*`, `okx_gateway`, `latency`.
- **Post-trade runtime:** `position_manager`, `journal`, `replay`, `reporting`.
- **Slow path intelligence:** `learning_loop/*`, `skill_intelligence/*`, `self_evolution/*`.
- **Contracts/config:** `models`, `config`.
- **Boundary interface:** `cli`.

## Dependency direction (must keep)
- adapters (`okx_gateway`, `nuwa_runtime`) -> provide data only.
- strategy modules cannot be imported by adapters.
- `learning_loop` / `self_evolution` cannot mutate runtime risk config directly.

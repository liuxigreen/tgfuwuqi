# Trade Core Architecture (v1.4)

- Fast Path: signal -> enrichment -> fast nuwa -> scoring -> risk -> decision -> order_intent -> demo/dry-run execution
- Slow Path: replay + daily review + deep nuwa + self-evolution proposals
- Fast Nuwa/Deep Nuwa separated
- Daily feedback loop writes journal -> review/report -> proposed_changes (human approval required)
- live auto trading stays disabled

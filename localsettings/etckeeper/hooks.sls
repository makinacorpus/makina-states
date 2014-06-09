{# hooks for etckeeper orchestration #}

etckeeper-run-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: etckeeper-post-run-hook

etckeeper-post-run-hook:
  mc_proxy.hook: []


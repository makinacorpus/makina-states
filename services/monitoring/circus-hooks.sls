{# Circus orchestration hooks #}
circus-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-restart
circus-post-restart:
  mc_proxy.hook: []

{# Circus orchestration hooks #}
supervisor-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: supervisor-post-install
      - mc_proxy: supervisor-pre-conf
      - mc_proxy: supervisor-post-conf
      - mc_proxy: supervisor-pre-restart
      - mc_proxy: supervisor-post-restart
supervisor-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: supervisor-pre-conf
      - mc_proxy: supervisor-post-conf
      - mc_proxy: supervisor-pre-restart
      - mc_proxy: supervisor-post-restart
supervisor-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: supervisor-post-conf
      - mc_proxy: supervisor-pre-restart
      - mc_proxy: supervisor-post-restart
supervisor-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: supervisor-pre-restart
      - mc_proxy: supervisor-post-restart

supervisor-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: supervisor-post-restart

supervisor-post-restart:
  mc_proxy.hook: []

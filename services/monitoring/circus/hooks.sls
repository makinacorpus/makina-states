{# Circus orchestration hooks #}
circus-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-install
      - mc_proxy: circus-pre-conf
      - mc_proxy: circus-post-conf
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-post-restart
circus-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-pre-conf
      - mc_proxy: circus-post-conf
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-post-restart
circus-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-conf
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-post-restart
circus-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-post-restart

circus-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-restart

circus-post-restart:
  mc_proxy.hook: []

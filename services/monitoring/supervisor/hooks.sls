{# supervisor orchestration hooks #}
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
    - require_in:
      - mc_proxy: supervisor-pre-hard-restart
      - mc_proxy: supervisor-post-hard-restart
    - watch_in:
      - mc_proxy: supervisor-pre-restart
      - mc_proxy: supervisor-post-restart
supervisor-pre-hard-restart:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: supervisor-post-hard-restart
      - mc_proxy: supervisor-pre-restart
      - mc_proxy: supervisor-post-restart
      - mc_proxy: supervisor-post-end
supervisor-post-hard-restart:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: supervisor-pre-restart
      - mc_proxy: supervisor-pre-restart
      - mc_proxy: supervisor-post-restart
      - mc_proxy: supervisor-post-end
supervisor-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: supervisor-post-restart
      - mc_proxy: supervisor-post-end
supervisor-post-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: supervisor-post-end
supervisor-post-end:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: supervisor-pre-disable
supervisor-pre-disable:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: supervisor-post-disable
supervisor-post-disable:
  mc_proxy.hook: []

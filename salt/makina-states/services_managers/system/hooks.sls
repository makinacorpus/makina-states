{# system orchestration hooks #}
system-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: system-post-install
      - mc_proxy: system-pre-conf
      - mc_proxy: system-post-conf
      - mc_proxy: system-pre-restart
      - mc_proxy: system-post-restart
system-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: system-pre-conf
      - mc_proxy: system-post-conf
      - mc_proxy: system-pre-restart
      - mc_proxy: system-post-restart
system-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: system-post-conf
      - mc_proxy: system-pre-restart
      - mc_proxy: system-post-restart
system-post-conf:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: system-pre-hard-restart
      - mc_proxy: system-post-hard-restart
    - watch_in:
      - mc_proxy: system-pre-restart
      - mc_proxy: system-post-restart
system-pre-hard-restart:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: system-post-hard-restart
      - mc_proxy: system-pre-restart
      - mc_proxy: system-post-restart
      - mc_proxy: system-post-end
system-post-hard-restart:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: system-pre-restart
      - mc_proxy: system-pre-restart
      - mc_proxy: system-post-restart
      - mc_proxy: system-post-end
system-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: system-post-restart
      - mc_proxy: system-post-end
system-post-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: system-post-end
system-post-end:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: system-pre-disable
system-pre-disable:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: system-post-disable
system-post-disable:
  mc_proxy.hook: []

{# circus orchestration hooks #}
circus-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-install
      - mc_proxy: circus-pre-conf2
      - mc_proxy: circus-post-conf
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-post-restart
circus-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-pre-conf2
      - mc_proxy: circus-post-conf
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-post-restart
circus-pre-conf2:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-conf
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-post-restart
{# retrocompatible hard restarter #}
circus-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-conf
      - mc_proxy: circus-pre-hard-restart
circus-post-conf:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: circus-pre-hard-restart
      - mc_proxy: circus-post-hard-restart
    - watch_in:
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-post-restart
circus-pre-hard-restart:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: circus-post-hard-restart
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-post-restart
      - mc_proxy: circus-post-end
circus-post-hard-restart:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-pre-restart
      - mc_proxy: circus-post-restart
      - mc_proxy: circus-post-end
circus-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-restart
      - mc_proxy: circus-post-end
circus-post-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-end
circus-pre-watchers:
  mc_proxy.hook:
    - require:
      - mc_proxy: circus-post-hard-restart
      - mc_proxy: circus-post-restart
    - watch_in:
      - mc_proxy: circus-pre-conf-watchers
circus-pre-conf-watchers:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-conf-watchers
circus-post-conf-watchers:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-watchers
circus-post-watchers:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-end
circus-post-end:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-pre-disable
circus-pre-disable:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: circus-post-disable
circus-post-disable:
  mc_proxy.hook: []

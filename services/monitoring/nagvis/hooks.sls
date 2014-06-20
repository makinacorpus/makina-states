{# Icinga-web orchestration hooks #}
nagvis-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nagvis-post-install
      - mc_proxy: nagvis-pre-conf
      - mc_proxy: nagvis-post-conf
      - mc_proxy: nagvis-pre-restart
      - mc_proxy: nagvis-post-restart
nagvis-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nagvis-pre-conf
      - mc_proxy: nagvis-post-conf
      - mc_proxy: nagvis-pre-restart
      - mc_proxy: nagvis-post-restart
nagvis-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nagvis-post-conf
      - mc_proxy: nagvis-pre-restart
      - mc_proxy: nagvis-post-restart
nagvis-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nagvis-pre-restart
      - mc_proxy: nagvis-post-restart

nagvis-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nagvis-post-restart

nagvis-post-restart:
  mc_proxy.hook: []

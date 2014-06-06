{# Icinga orchestration hooks #}
icinga-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-post-install
      - mc_proxy: icinga-pre-conf
      - mc_proxy: icinga-post-conf
      - mc_proxy: icinga-pre-restart
      - mc_proxy: icinga-post-restart
icinga-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-pre-conf
      - mc_proxy: icinga-post-conf
      - mc_proxy: icinga-pre-restart
      - mc_proxy: icinga-post-restart
icinga-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-post-conf
      - mc_proxy: icinga-pre-restart
      - mc_proxy: icinga-post-restart
icinga-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-pre-restart
      - mc_proxy: icinga-post-restart

icinga-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga-post-restart

icinga-post-restart:
  mc_proxy.hook: []

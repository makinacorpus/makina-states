{# Icinga-web orchestration hooks #}
icinga_web-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_web-post-install
      - mc_proxy: icinga_web-pre-conf
      - mc_proxy: icinga_web-post-conf
      - mc_proxy: icinga_web-pre-restart
      - mc_proxy: icinga_web-post-restart
icinga_web-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_web-pre-conf
      - mc_proxy: icinga_web-post-conf
      - mc_proxy: icinga_web-pre-restart
      - mc_proxy: icinga_web-post-restart
icinga_web-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_web-post-conf
      - mc_proxy: icinga_web-pre-restart
      - mc_proxy: icinga_web-post-restart
icinga_web-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_web-pre-restart
      - mc_proxy: icinga_web-post-restart

icinga_web-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_web-post-restart

icinga_web-post-restart:
  mc_proxy.hook: []

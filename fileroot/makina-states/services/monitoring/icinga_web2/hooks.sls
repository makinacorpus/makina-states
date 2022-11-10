{# Icinga-web orchestration hooks #}
icinga_web2-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_web2-post-install
      - mc_proxy: icinga_web2-pre-conf
      - mc_proxy: icinga_web2-post-conf
      - mc_proxy: icinga_web2-pre-restart
      - mc_proxy: icinga_web2-post-restart
icinga_web2-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_web2-pre-conf
      - mc_proxy: icinga_web2-post-conf
      - mc_proxy: icinga_web2-pre-restart
      - mc_proxy: icinga_web2-post-restart
icinga_web2-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_web2-post-conf
      - mc_proxy: icinga_web2-pre-restart
      - mc_proxy: icinga_web2-post-restart
icinga_web2-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_web2-pre-restart
      - mc_proxy: icinga_web2-post-restart

icinga_web2-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_web2-post-restart

icinga_web2-post-restart:
  mc_proxy.hook: []

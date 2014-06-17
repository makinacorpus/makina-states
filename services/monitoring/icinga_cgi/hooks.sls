{# Icinga-web orchestration hooks #}
icinga_cgi-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_cgi-post-install
      - mc_proxy: icinga_cgi-pre-conf
      - mc_proxy: icinga_cgi-post-conf
      - mc_proxy: icinga_cgi-pre-restart
      - mc_proxy: icinga_cgi-post-restart
icinga_cgi-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_cgi-pre-conf
      - mc_proxy: icinga_cgi-post-conf
      - mc_proxy: icinga_cgi-pre-restart
      - mc_proxy: icinga_cgi-post-restart
icinga_cgi-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_cgi-post-conf
      - mc_proxy: icinga_cgi-pre-restart
      - mc_proxy: icinga_cgi-post-restart
icinga_cgi-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_cgi-pre-restart
      - mc_proxy: icinga_cgi-post-restart

icinga_cgi-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: icinga_cgi-post-restart

icinga_cgi-post-restart:
  mc_proxy.hook: []

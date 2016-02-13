{# Icinga-web orchestration hooks #}
uwsgi-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: uwsgi-post-install
      - mc_proxy: uwsgi-pre-conf
      - mc_proxy: uwsgi-post-conf
      - mc_proxy: uwsgi-pre-restart
      - mc_proxy: uwsgi-post-restart
uwsgi-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: uwsgi-pre-conf
      - mc_proxy: uwsgi-post-conf
      - mc_proxy: uwsgi-pre-restart
      - mc_proxy: uwsgi-post-restart
uwsgi-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: uwsgi-post-conf
      - mc_proxy: uwsgi-pre-restart
      - mc_proxy: uwsgi-post-restart
uwsgi-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: uwsgi-pre-restart
      - mc_proxy: uwsgi-post-restart

uwsgi-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: uwsgi-post-restart

uwsgi-post-restart:
  mc_proxy.hook: []

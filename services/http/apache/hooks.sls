makina-apache-pre-inst:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-apache-post-inst
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-restart
      - mc_proxy: makina-apache-post-restart
      - mc_proxy: makina-apache-post-pkgs

makina-apache-post-pkgs:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-apache-post-inst
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-restart
      - mc_proxy: makina-apache-post-restart

makina-apache-post-inst:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-restart
      - mc_proxy: makina-apache-post-restart

makina-apache-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-restart
      - mc_proxy: makina-apache-post-restart

makina-apache-vhostconf:
  mc_proxy.hook:
    - watch:
      - mc_proxy: makina-apache-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-post-conf

makina-apache-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-apache-pre-reload
      - mc_proxy: makina-apache-post-reload

makina-apache-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-apache-post-restart

makina-apache-post-restart:
  mc_proxy.hook: []

makina-apache-pre-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-apache-post-reload

makina-apache-post-reload:
  mc_proxy.hook: []

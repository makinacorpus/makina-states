memcached-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: memcached-post-install
      - mc_proxy: memcached-pre-conf
      - mc_proxy: memcached-post-conf
      - mc_proxy: memcached-pre-reload
memcached-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: memcached-pre-conf
      - mc_proxy: memcached-post-conf
      - mc_proxy: memcached-pre-reload

memcached-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: memcached-post-conf
      - mc_proxy: memcached-pre-reload
      - mc_proxy: memcached-check-conf
memcached-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: memcached-pre-reload
      - mc_proxy: memcached-check-conf
memcached-check-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: memcached-pre-reload
      - mc_proxy: memcached-pre-restart
memcached-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: memcached-post-restart
memcached-post-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: memcached-post-end
memcached-pre-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: memcached-post-reload
memcached-post-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: memcached-post-end
memcached-post-end:
  mc_proxy.hook: []

{# Circus orchestration hooks #}
redis-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: redis-post-install
      - mc_proxy: redis-pre-conf
      - mc_proxy: redis-post-conf
      - mc_proxy: redis-pre-restart
      - mc_proxy: redis-post-restart
redis-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: redis-pre-conf
      - mc_proxy: redis-post-conf
      - mc_proxy: redis-pre-restart
      - mc_proxy: redis-post-restart
      - mc_proxy: redis-pre-hardrestart
redis-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: redis-post-conf
      - mc_proxy: redis-pre-restart
      - mc_proxy: redis-post-restart
redis-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: redis-pre-hardrestart
      - mc_proxy: redis-post-hardrestart

redis-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: redis-post-restart

redis-post-restart:
  mc_proxy.hook: []

redis-pre-hardrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: redis-post-hardrestart

redis-post-hardrestart:
  mc_proxy.hook: []


redis-db-create-hook:
  mc_proxy.hook: []
redis-db-create-user-hook:
  mc_proxy.hook: []
redis-db-grant-hook:
  mc_proxy.hook: []


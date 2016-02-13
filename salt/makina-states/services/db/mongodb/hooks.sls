{# Circus orchestration hooks #}
mongodb-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mongodb-post-install
      - mc_proxy: mongodb-pre-conf
      - mc_proxy: mongodb-post-conf
      - mc_proxy: mongodb-pre-restart
      - mc_proxy: mongodb-post-restart
mongodb-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mongodb-pre-conf
      - mc_proxy: mongodb-post-conf
      - mc_proxy: mongodb-pre-restart
      - mc_proxy: mongodb-post-restart
      - mc_proxy: mongodb-pre-hardrestart
mongodb-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mongodb-post-conf
      - mc_proxy: mongodb-pre-restart
      - mc_proxy: mongodb-post-restart
mongodb-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mongodb-pre-restart
      - mc_proxy: mongodb-post-restart

mongodb-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mongodb-post-restart

mongodb-post-restart:
  mc_proxy.hook: []

mongodb-pre-hardrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mongodb-post-hardrestart

mongodb-post-hardrestart:
  mc_proxy.hook: []


mongodb-db-create-hook:
  mc_proxy.hook: []
mongodb-db-create-user-hook:
  mc_proxy.hook: []
mongodb-db-grant-hook:
  mc_proxy.hook: []


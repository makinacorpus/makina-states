{# Circus orchestration hooks #}
rabbitmq-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rabbitmq-post-install
      - mc_proxy: rabbitmq-pre-conf
      - mc_proxy: rabbitmq-post-conf
      - mc_proxy: rabbitmq-pre-restart
      - mc_proxy: rabbitmq-post-restart
rabbitmq-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rabbitmq-pre-conf
      - mc_proxy: rabbitmq-post-conf
      - mc_proxy: rabbitmq-pre-restart
      - mc_proxy: rabbitmq-post-restart
      - mc_proxy: rabbitmq-pre-hardrestart
rabbitmq-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rabbitmq-post-conf
      - mc_proxy: rabbitmq-pre-restart
      - mc_proxy: rabbitmq-post-restart
rabbitmq-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rabbitmq-pre-restart
      - mc_proxy: rabbitmq-post-restart

rabbitmq-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rabbitmq-post-restart

rabbitmq-post-restart:
  mc_proxy.hook: []

rabbitmq-pre-hardrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rabbitmq-post-hardrestart

rabbitmq-post-hardrestart:
  mc_proxy.hook: []


rabbitmq-db-create-hook:
  mc_proxy.hook: []
rabbitmq-db-create-user-hook:
  mc_proxy.hook: []
rabbitmq-db-grant-hook:
  mc_proxy.hook: []


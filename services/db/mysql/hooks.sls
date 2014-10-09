{# mysql orchestration hooks #}
mysql-db-create-hook:
  mc_proxy.hook: []
mysql-db-create-user-hook:
  mc_proxy.hook: []
mysql-db-grant-hook:
  mc_proxy.hook: []
mysql-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-post-install-hook
      - mc_proxy: mysql-pre-conf-hook
      - mc_proxy: mysql-post-conf-hook
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: mysql-post-default-tuning-hook
      - mc_proxy: mysql-post-restart-hook

mysql-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-pre-conf-hook
      - mc_proxy: mysql-post-conf-hook
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: mysql-post-default-tuning-hook
      - mc_proxy: mysql-post-restart-hook

mysql-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-post-conf-hook
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-post-default-tuning-hook

mysql-post-default-tuning-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: mysql-post-hardrestart-hook
      - mc_proxy: mysql-post-conf-hook

mysql-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: mysql-post-hardrestart-hook

mysql-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-post-restart-hook

mysql-post-restart-hook:
  mc_proxy.hook: []

mysql-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-post-hardrestart-hook

mysql-post-hardrestart-hook:
  mc_proxy.hook: []


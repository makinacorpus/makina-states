{# mysql orchestration hooks #}
mysql-db-create-hook:
  mc_proxy.hook:
    - watch:
      - mc_proxy: mysql-setup-access
      - mc_proxy: mysql-post-hardrestart-hook
      - mc_proxy: mysql-post-restart-hook
mysql-db-create-user-hook:
  mc_proxy.hook:
    - watch:
      - mc_proxy: mysql-setup-access
      - mc_proxy: mysql-post-hardrestart-hook
      - mc_proxy: mysql-post-restart-hook
mysql-db-grant-hook:
  mc_proxy.hook:
    - watch:
      - mc_proxy: mysql-setup-access
      - mc_proxy: mysql-db-create-hook
      - mc_proxy: mysql-post-hardrestart-hook
      - mc_proxy: mysql-post-restart-hook
mysql-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-post-install-hook
      - mc_proxy: mysql-pre-conf-hook
      - mc_proxy: mysql-post-default-tuning-hook
      - mc_proxy: mysql-post-conf-hook
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-pre-hardrestart-hook
      - mc_proxy: mysql-post-hardrestart-hook
mysql-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-pre-conf-hook
      - mc_proxy: mysql-post-default-tuning-hook
      - mc_proxy: mysql-post-conf-hook
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-pre-hardrestart-hook
      - mc_proxy: mysql-post-hardrestart-hook
mysql-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-post-default-tuning-hook
      - mc_proxy: mysql-post-conf-hook
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-pre-hardrestart-hook
      - mc_proxy: mysql-post-hardrestart-hook
mysql-post-default-tuning-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-post-conf-hook
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-pre-hardrestart-hook
      - mc_proxy: mysql-post-hardrestart-hook
mysql-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-pre-hardrestart-hook
      - mc_proxy: mysql-post-hardrestart-hook
mysql-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-post-restart-hook
mysql-post-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-setup-access-pre
mysql-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-post-hardrestart-hook
mysql-post-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-setup-access-pre
mysql-setup-access-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mysql-setup-access
mysql-setup-access:
  mc_proxy.hook: []

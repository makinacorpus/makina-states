{# dovecot orchestration hooks #}
dovecot-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dovecot-post-install-hook
      - mc_proxy: dovecot-pre-conf-hook
      - mc_proxy: dovecot-post-conf-hook
      - mc_proxy: dovecot-pre-restart-hook
      - mc_proxy: dovecot-post-restart-hook

dovecot-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dovecot-pre-conf-hook
      - mc_proxy: dovecot-post-conf-hook
      - mc_proxy: dovecot-pre-restart-hook
      - mc_proxy: dovecot-post-restart-hook

dovecot-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dovecot-post-conf-hook
      - mc_proxy: dovecot-pre-restart-hook
      - mc_proxy: dovecot-post-restart-hook

dovecot-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dovecot-pre-restart-hook
      - mc_proxy: dovecot-post-restart-hook

dovecot-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dovecot-post-restart-hook

dovecot-post-restart-hook:
  mc_proxy.hook: []


dovecot-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dovecot-post-hardrestart-hook

dovecot-post-hardrestart-hook:
  mc_proxy.hook: []


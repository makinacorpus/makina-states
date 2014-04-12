{# postfix orchestration hooks #}
postfix-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-post-install-hook
      - mc_proxy: postfix-pre-conf-hook
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook
      - mc_proxy: postfix-post-restart-hook

postfix-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-pre-conf-hook
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook
      - mc_proxy: postfix-post-restart-hook

postfix-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook
      - mc_proxy: postfix-post-restart-hook

postfix-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-pre-restart-hook
      - mc_proxy: postfix-post-restart-hook

postfix-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-post-restart-hook

postfix-post-restart-hook:
  mc_proxy.hook: []


postfix-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-post-hardrestart-hook

postfix-post-hardrestart-hook:
  mc_proxy.hook: []


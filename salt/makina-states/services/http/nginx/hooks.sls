nginx-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nginx-post-install-hook
      - mc_proxy: nginx-pre-conf-hook
      - mc_proxy: nginx-post-conf-hook
      - mc_proxy: nginx-pre-restart-hook
      - mc_proxy: nginx-post-restart-hook

nginx-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nginx-pre-conf-hook
      - mc_proxy: nginx-post-conf-hook
      - mc_proxy: nginx-pre-restart-hook
      - mc_proxy: nginx-post-restart-hook

nginx-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nginx-post-conf-hook
      - mc_proxy: nginx-pre-restart-hook
      - mc_proxy: nginx-post-restart-hook

nginx-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nginx-pre-restart-hook
      - mc_proxy: nginx-post-restart-hook

nginx-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nginx-post-hardrestart-hook

nginx-post-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nginx-pre-restart-hook

nginx-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nginx-post-restart-hook

nginx-post-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nginx-pre-disable

nginx-pre-disable:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nginx-post-disable

nginx-post-disable:
  mc_proxy.hook: []



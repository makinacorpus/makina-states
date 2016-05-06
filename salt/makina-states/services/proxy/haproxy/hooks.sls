{# haproxy orchestration hooks #}
haproxy-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: haproxy-post-install-hook
      - mc_proxy: haproxy-pre-conf-hook
      - mc_proxy: haproxy-post-conf-hook
      - mc_proxy: haproxy-pre-restart-hook
      - mc_proxy: haproxy-post-restart-hook

haproxy-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: haproxy-pre-conf-hook
      - mc_proxy: haproxy-post-conf-hook
      - mc_proxy: haproxy-pre-restart-hook
      - mc_proxy: haproxy-post-restart-hook

haproxy-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: haproxy-post-conf-hook
      - mc_proxy: haproxy-pre-restart-hook
      - mc_proxy: haproxy-post-restart-hook

haproxy-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: haproxy-pre-restart-hook
      - mc_proxy: haproxy-post-restart-hook

haproxy-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: haproxy-post-restart-hook

haproxy-post-restart-hook:
  mc_proxy.hook: []

haproxy-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: haproxy-post-hardrestart-hook

haproxy-post-hardrestart-hook:
  mc_proxy.hook: []


{# mumble orchestration hooks #}
mumble-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mumble-post-install-hook
      - mc_proxy: mumble-pre-conf-hook
      - mc_proxy: mumble-post-conf-hook
      - mc_proxy: mumble-pre-restart-hook
      - mc_proxy: mumble-post-restart-hook

mumble-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mumble-pre-conf-hook
      - mc_proxy: mumble-post-conf-hook
      - mc_proxy: mumble-pre-restart-hook
      - mc_proxy: mumble-post-restart-hook

mumble-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mumble-post-conf-hook
      - mc_proxy: mumble-pre-restart-hook
      - mc_proxy: mumble-post-restart-hook

mumble-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mumble-pre-restart-hook
      - mc_proxy: mumble-post-restart-hook

mumble-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mumble-post-restart-hook

mumble-post-restart-hook:
  mc_proxy.hook: []


mumble-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: mumble-post-hardrestart-hook

mumble-post-hardrestart-hook:
  mc_proxy.hook: []


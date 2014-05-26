{# ulogd orchestration hooks #}
ulogd-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ulogd-post-install-hook
      - mc_proxy: ulogd-pre-conf-hook
      - mc_proxy: ulogd-post-conf-hook
      - mc_proxy: ulogd-pre-restart-hook
      - mc_proxy: ulogd-post-restart-hook

ulogd-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ulogd-pre-conf-hook
      - mc_proxy: ulogd-post-conf-hook
      - mc_proxy: ulogd-pre-restart-hook
      - mc_proxy: ulogd-post-restart-hook

ulogd-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ulogd-post-conf-hook
      - mc_proxy: ulogd-pre-restart-hook
      - mc_proxy: ulogd-post-restart-hook

ulogd-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ulogd-pre-restart-hook
      - mc_proxy: ulogd-post-restart-hook

ulogd-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ulogd-post-restart-hook

ulogd-post-restart-hook:
  mc_proxy.hook: []


ulogd-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ulogd-post-hardrestart-hook

ulogd-post-hardrestart-hook:
  mc_proxy.hook: []


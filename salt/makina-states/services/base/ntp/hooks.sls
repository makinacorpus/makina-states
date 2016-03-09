{# ntp orchestration hooks #}
ntp-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ntp-post-install-hook
      - mc_proxy: ntp-pre-conf-hook
      - mc_proxy: ntp-post-conf-hook
      - mc_proxy: ntp-pre-restart-hook
      - mc_proxy: ntp-post-restart-hook

ntp-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ntp-pre-conf-hook
      - mc_proxy: ntp-post-conf-hook
      - mc_proxy: ntp-pre-restart-hook
      - mc_proxy: ntp-post-restart-hook

ntp-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ntp-post-conf-hook
      - mc_proxy: ntp-pre-restart-hook
      - mc_proxy: ntp-post-restart-hook

ntp-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ntp-pre-restart-hook
      - mc_proxy: ntp-post-restart-hook

ntp-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ntp-post-restart-hook

ntp-post-restart-hook:
  mc_proxy.hook: []


ntp-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ntp-post-hardrestart-hook

ntp-post-hardrestart-hook:
  mc_proxy.hook: []


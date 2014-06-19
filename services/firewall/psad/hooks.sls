
{# psad orchestration hooks #}
psad-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: psad-post-install-hook
      - mc_proxy: psad-pre-conf-hook
      - mc_proxy: psad-post-conf-hook
      - mc_proxy: psad-pre-restart-hook
      - mc_proxy: psad-post-restart-hook

psad-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: psad-pre-conf-hook
      - mc_proxy: psad-post-conf-hook
      - mc_proxy: psad-pre-restart-hook
      - mc_proxy: psad-post-restart-hook

psad-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: psad-post-conf-hook
      - mc_proxy: psad-pre-restart-hook
      - mc_proxy: psad-post-restart-hook

psad-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: psad-pre-restart-hook
      - mc_proxy: psad-post-restart-hook

psad-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: psad-post-restart-hook

psad-post-restart-hook:
  mc_proxy.hook: []


psad-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: psad-post-hardrestart-hook

psad-post-hardrestart-hook:
  mc_proxy.hook: []


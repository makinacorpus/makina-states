
{# burp orchestration hooks #}
burp-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: burp-post-install-hook
      - mc_proxy: burp-pre-conf-hook
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-pre-restart-hook
      - mc_proxy: burp-post-restart-hook

burp-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: burp-pre-conf-hook
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-pre-restart-hook
      - mc_proxy: burp-post-restart-hook

burp-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: burp-post-conf-hook
      - mc_proxy: burp-pre-restart-hook
      - mc_proxy: burp-post-restart-hook

burp-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: burp-pre-restart-hook
      - mc_proxy: burp-post-restart-hook

burp-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: burp-post-restart-hook


burp-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: burp-post-hardrestart-hook

burp-post-restart-hook:
  mc_proxy.hook:
   - watch_in:
      - mc_proxy: burp-post-gen-sync
      - mc_proxy: burp-post-sync

burp-post-hardrestart-hook:
  mc_proxy.hook:
   - watch_in:
      - mc_proxy: burp-post-gen-sync
      - mc_proxy: burp-post-sync

burp-post-gen-sync:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: burp-post-sync

burp-post-sync:
  mc_proxy.hook: []


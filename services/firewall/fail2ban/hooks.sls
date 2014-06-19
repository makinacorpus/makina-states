{# fail2ban orchestration hooks #}
fail2ban-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: fail2ban-post-install-hook
      - mc_proxy: fail2ban-pre-conf-hook
      - mc_proxy: fail2ban-post-conf-hook
      - mc_proxy: fail2ban-pre-restart-hook
      - mc_proxy: fail2ban-post-restart-hook

fail2ban-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: fail2ban-pre-conf-hook
      - mc_proxy: fail2ban-post-conf-hook
      - mc_proxy: fail2ban-pre-restart-hook
      - mc_proxy: fail2ban-post-restart-hook

fail2ban-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: fail2ban-post-conf-hook
      - mc_proxy: fail2ban-pre-restart-hook
      - mc_proxy: fail2ban-post-restart-hook

fail2ban-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: fail2ban-pre-restart-hook
      - mc_proxy: fail2ban-post-restart-hook

fail2ban-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: fail2ban-post-restart-hook

fail2ban-post-restart-hook:
  mc_proxy.hook: []


fail2ban-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: fail2ban-post-hardrestart-hook

fail2ban-post-hardrestart-hook:
  mc_proxy.hook: []


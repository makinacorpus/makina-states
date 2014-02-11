{#- FTP servers configuration hooks #}

ftpd-pre-installation-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ftpd-post-installation-hook
      - mc_proxy: ftpd-pre-configuration-hook
      - mc_proxy: ftpd-post-configuration-hook
      - mc_proxy: ftpd-pre-restart-hook
      - mc_proxy: ftpd-post-restart-hook

ftpd-post-installation-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ftpd-pre-configuration-hook
      - mc_proxy: ftpd-post-configuration-hook
      - mc_proxy: ftpd-pre-restart-hook
      - mc_proxy: ftpd-post-restart-hook

ftpd-pre-configuration-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ftpd-post-configuration-hook
      - mc_proxy: ftpd-pre-restart-hook
      - mc_proxy: ftpd-post-restart-hook

ftpd-post-configuration-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ftpd-pre-restart-hook
      - mc_proxy: ftpd-post-restart-hook


ftpd-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ftpd-post-restart-hook

ftpd-post-restart-hook:
  mc_proxy.hook: []


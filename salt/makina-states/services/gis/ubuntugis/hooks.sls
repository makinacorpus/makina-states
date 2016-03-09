ubuntugis-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ubuntugis-post-install-hook
      - mc_proxy: ubuntugis-pre-conf-hook
      - mc_proxy: ubuntugis-post-conf-hook
      - mc_proxy: ubuntugis-pre-restart-hook
      - mc_proxy: ubuntugis-post-restart-hook

ubuntugis-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ubuntugis-pre-conf-hook
      - mc_proxy: ubuntugis-post-conf-hook
      - mc_proxy: ubuntugis-pre-restart-hook
      - mc_proxy: ubuntugis-post-restart-hook

ubuntugis-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ubuntugis-post-conf-hook
      - mc_proxy: ubuntugis-pre-restart-hook
      - mc_proxy: ubuntugis-post-restart-hook

ubuntugis-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ubuntugis-pre-restart-hook
      - mc_proxy: ubuntugis-post-restart-hook

ubuntugis-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ubuntugis-post-restart-hook

ubuntugis-post-restart-hook:
  mc_proxy.hook: []

ubuntugis-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ubuntugis-post-hardrestart-hook

ubuntugis-post-hardrestart-hook:
  mc_proxy.hook: []


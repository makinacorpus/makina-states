ssl-certs-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ssl-certs-pre-hook
      - mc_proxy: ssl-certs-post-install
ssl-certs-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ssl-certs-pre-hook
ssl-certs-pre-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ssl-certs-post-hook
ssl-certs-clean-certs:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - mc_proxy: ssl-certs-post-hook
ssl-certs-post-hook:
  mc_proxy.hook: []

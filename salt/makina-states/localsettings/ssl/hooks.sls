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
      - mc_proxy: ssl-certs-clean-certs-pre
ssl-certs-clean-certs-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - mc_proxy: ssl-certs-post-hook
      - mc_proxy: ssl-certs-clean-certs-post
ssl-certs-clean-certs-post:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - mc_proxy: ssl-certs-post-hook

ssl-certs-trust-certs-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ssl-certs-pre-hook
      - mc_proxy: ssl-certs-clean-certs-post
    - watch_in:
      - mc_proxy: ssl-certs-post-hook
      - mc_proxy: ssl-certs-trust-certs-post
ssl-certs-trust-certs-post:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - mc_proxy: ssl-certs-post-hook
ssl-certs-post-hook:
  mc_proxy.hook: []

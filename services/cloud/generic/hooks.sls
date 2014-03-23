pre-reverseproxy-setup:
  mc_proxy.hook:
    - watch_in
      - mc_proxy: post-reverseproxy-setup

post-reverseproxy-setup:
  mc_proxy.hook: []


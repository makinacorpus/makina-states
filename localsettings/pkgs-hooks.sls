before-pkg-install-proxy:
  mc_proxy.hook:
    - watch_in:
      mc_proxy: after-pkg-install-proxy
after-pkg-install-proxy:
  mc_proxy.hook: []


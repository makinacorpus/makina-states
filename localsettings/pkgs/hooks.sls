before-pkgmgr-config-proxy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: after-base-pkgmgr-config-proxy
      - mc_proxy: after-pkgmgr-config-proxy
      - mc_proxy: before-pkg-install-proxy
      - mc_proxy: after-pkg-install-proxy

after-base-pkgmgr-config-proxy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: after-pkgmgr-config-proxy
      - mc_proxy: before-pkg-install-proxy
      - mc_proxy: after-pkg-install-proxy

after-pkgmgr-config-proxy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: before-pkg-install-proxy
      - mc_proxy: after-pkg-install-proxy

before-pkg-install-proxy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: after-pkg-install-proxy

after-pkg-install-proxy:
  mc_proxy.hook: []

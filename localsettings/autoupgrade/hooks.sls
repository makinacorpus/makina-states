include:
  - makina-states.localsettings.pkgs.hooks

before-au-pkg-install-proxy:
  mc_proxy.hook:
    - watch:
      - mc_proxy: after-pkg-install-proxy
    - watch_in:
      - mc_proxy: after-au-pkg-conf-proxy

after-au-pkg-install-proxy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: before-au-pkg-conf-proxy

before-au-pkg-conf-proxy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: after-au-pkg-conf-proxy

after-au-pkg-conf-proxy:
  mc_proxy.hook: []

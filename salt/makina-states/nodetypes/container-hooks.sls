makina-lxc-proxy-pkgs-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-lxc-proxy-pkgs

makina-lxc-proxy-pkgs:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-lxc-proxy-cfg

makina-lxc-proxy-cfg:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-lxc-proxy-dep

makina-lxc-proxy-dep:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-lxc-proxy-build

makina-lxc-proxy-build:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-lxc-proxy-mark

makina-lxc-proxy-mark:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-lxc-proxy-cleanup

makina-lxc-proxy-cleanup:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-lxc-proxy-end

makina-lxc-proxy-end:
  mc_proxy.hook: []

include:
  - makina-states.localsettings.apparmor.hooks
lxc-pre-pkg:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ms-apparmor-post
    - watch_in:
      - mc_proxy: lxc-pre-conf
      - mc_proxy: lxc-post-conf
      - mc_proxy: lxc-post-pkg
      - mc_proxy: lxc-pre-restart
      - mc_proxy: lxc-post-inst

lxc-post-pkg:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: lxc-pre-conf
      - mc_proxy: lxc-post-conf
      - mc_proxy: lxc-pre-restart
      - mc_proxy: lxc-post-inst

lxc-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: lxc-post-conf
      - mc_proxy: lxc-pre-restart
      - mc_proxy: lxc-post-inst

lxc-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: lxc-pre-restart
      - mc_proxy: lxc-post-inst

lxc-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: lxc-post-inst

lxc-post-inst:
  mc_proxy.hook: []

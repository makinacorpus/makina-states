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

lxc-services-others-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: lxc-services-others-post
lxc-services-others-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: lxc-net-services-enabling-pre
lxc-net-services-enabling-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: lxc-net-services-enabling-post
lxc-net-services-enabling-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: lxc-services-enabling-pre
lxc-post-inst:
  mc_proxy.hook: 
    - watch_in:
      - mc_proxy: lxc-services-enabling-pre
lxc-services-enabling-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: lxc-services-enabling-post
lxc-services-enabling-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: lxc-post-end
lxc-post-end:
  mc_proxy.hook: []

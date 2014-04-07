include:
  - makina-states.services.virt.lxc.hooks

lxc-other-svc:
  service.running:
    - names:
      - apparmor
    - enable: True
    - enable: True
    - watch:
      - mc_proxy: lxc-pre-restart
    - watch_in:
      - services: lxc-services-enabling

lxc-services-enabling:
  service.running:
    - reload: true
    - enable: true
    - names:
      - lxc
      - lxc-net
    - watch:
      - mc_proxy: lxc-pre-restart
    - watch_in:
      - mc_proxy: lxc-post-inst

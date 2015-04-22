include:
  - makina-states.services.virt.lxc.hooks
  - makina-states.services.virt.cgroups
{% if salt['mc_controllers.mastersalt_mode']() %}
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
      - lxc-net-makina
    - watch:
      - mc_proxy: lxc-pre-restart
    - watch_in:
      - mc_proxy: lxc-post-inst
{% endif %}

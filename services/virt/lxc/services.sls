include:
  - makina-states.services.virt.lxc.hooks
  - makina-states.services.virt.cgroups
{% if salt['mc_controllers.mastersalt_mode']() %}
lxc-other-svc:
  service.running:
    - names:
      - apparmor
    - enable: True
    - watch:
      - mc_proxy: lxc-pre-restart
    - watch_in:
      - services: lxc-services-enabling

lxc-services-net-enabling:
  service.running:
    - enable: true
    - names:
      - lxc-net
      - lxc-net-makina
    - watch:
      - mc_proxy: lxc-pre-restart
      - service: lxc-other-svc
    - watch_in:
      - mc_proxy: lxc-post-inst

lxc-services-enabling:
  service.running:
    - enable: true
    - names:
      - lxc
    - require:
      - mc_proxy: lxc-pre-restart
      - service: lxc-services-net-enabling
      - service: lxc-other-svc
    - require:
      - mc_proxy: lxc-post-inst
    - watch:
      - mc_proxy: lxc-post-pkg
{% endif %}

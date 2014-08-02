include:
  - makina-states.services.virt.lxc.hooks
  - makina-states.services.virt.docker.hooks
  - makina-states.services.firewall.firewalld.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.services.firewall.shorewall.disable
  - makina-states.localsettings.network
  - makina-states.services.base.dbus
  - makina-states.services.firewall.firewalld.prerequisites
  - makina-states.services.firewall.firewalld.configuration
  - makina-states.services.firewall.firewalld.services
{% endif %}
firewalld-orchestrate:
  mc_proxy.hook:
    - watch:
      - mc_proxy: lxc-post-inst
      - mc_proxy: docker-post-inst
    - watch_in:
      - mc_proxy: firewalld-preconf

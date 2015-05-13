{{ salt['mc_macros.unregister']('services', 'firewall.shorewall') }}
{{ salt['mc_macros.register']('services', 'firewall.firewalld') }}

include:
  - makina-states.services.virt.lxc.hooks
  - makina-states.services.virt.docker.hooks
  - makina-states.services.firewall.firewalld.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
{% if salt['mc_services.registry']()['is'].get('firewall.shorewall') %}
  - makina-states.services.firewall.shorewall.disable
{% endif %}
  - makina-states.localsettings.network
  - makina-states.services.firewall.firewalld.prerequisites
  - makina-states.services.firewall.firewalld.configuration
  - makina-states.services.firewall.firewalld.service
  - makina-states.services.base.dbus
{% endif %}
firewalld-orchestrate:
  mc_proxy.hook:
    - watch:
      - mc_proxy: lxc-post-inst
      - mc_proxy: docker-post-inst
    - watch_in:
      - mc_proxy: firewalld-preconf

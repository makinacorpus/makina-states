{{ salt['mc_macros.register']('services', 'firewall.shorewall') }}

include:
  - makina-states.services.virt.lxc.hooks
  - makina-states.services.virt.docker.hooks
  - makina-states.services.firewall.shorewall.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.localsettings.localrc
  - makina-states.services.firewall.shorewall.prerequisites
  - makina-states.services.firewall.shorewall.configuration
  - makina-states.services.firewall.shorewall.service
{% endif %}
shorewall-orchestrate:
  mc_proxy.hook:
    - watch:
      - file: rc-local-d
      - mc_proxy: lxc-post-inst
      - mc_proxy: docker-post-inst
    - watch_in:
      - mc_proxy: shorewall-preconf

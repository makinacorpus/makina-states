{% set firewalld = salt['mc_services.registry']()['is'].get('firewall.firewalld') %}
{% if not firewalld %}
{{ salt['mc_macros.register']('services', 'firewall.shorewall') }}
{% endif %}
include:
  - makina-states.localsettings.network
  - makina-states.services.virt.lxc.hooks
  - makina-states.services.virt.docker.hooks
  - makina-states.services.firewall.shorewall.hooks
{% if firewalld %}
  - makina-states.services.firewall.shorewall.disable
{% else %}
  - makina-states.localsettings.localrc
  - makina-states.services.firewall.shorewall.prerequisites
  - makina-states.services.firewall.shorewall.configuration
  - makina-states.services.firewall.shorewall.services
{% endif %}
shorewall-orchestrate:
  mc_proxy.hook:
    - watch:
      - file: rc-local-d
      - mc_proxy: lxc-post-inst
      - mc_proxy: docker-post-inst
    - watch_in:
      - mc_proxy: shorewall-preconf

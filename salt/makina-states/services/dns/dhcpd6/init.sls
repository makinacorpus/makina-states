{{ salt['mc_macros.register']('services', 'dns.dhcpd6') }}
include:
{% if salt['mc_services.registry']().is['dns.bind'] %}
  - makina-states.services.dns.bind
{%endif %}
  - makina-states.services.dns.dhcpd6.hooks
  - makina-states.services.dns.dhcpd6.prerequisites
  - makina-states.services.dns.dhcpd6.configuration
  - makina-states.services.dns.dhcpd6.services
{% if salt['mc_services.registry']().is['dns.bind'] %}
dhcpd6-bind-orchestrate:
  mc_proxy.hook:
    - watch:
      - mc_proxy: bind-post-end
    - watch_in:
      - mc_proxy: dhcpd6-pre-install

{% endif %}

{{ salt['mc_macros.register']('services', 'dns.dhcpd') }}
include:
{% if salt['mc_services.registry']().is['dns.bind'] %}
#  - makina-states.services.dns.bind
{%endif %}
  - makina-states.services.dns.dhcpd.hooks
  - makina-states.services.dns.dhcpd.prerequisites
  - makina-states.services.dns.dhcpd.configuration
  - makina-states.services.dns.dhcpd.services
{% if salt['mc_services.registry']().is['dns.bind'] %}
#dhcpd-bind-orchestrate:
#  mc_proxy.hook:
#    - watch:
#      - mc_proxy: bind-post-end
#    - watch_in:
#      - mc_proxy: dhcpd-pre-install
#
{% endif %}

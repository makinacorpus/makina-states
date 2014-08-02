{% if salt['mc_services.registry']().is['dns.bind'] %}
include:
- makina-states.services.dns.bind
{% endif %}

dnsconf-dummy:
  mc_proxy.hook: []


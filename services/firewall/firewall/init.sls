{{ salt['mc_macros.register']('services', 'firewall.firewall') }}
{% macro fw(install=False)%}
{% set incs = [] %}
{% if salt['mc_services.registry']()['is'].get('firewall.ms_iptables') %}
{% do incs.append('makina-states.services.firewall.ms_iptables') %}
{% elif salt['mc_services.registry']()['is'].get('firewall.firewalld') %}
{% do incs.append('makina-states.services.firewall.firewalld') %}
{% elif salt['mc_services.registry']()['is'].get('firewall.shorewall') %}
{% do incs.append('makina-states.services.firewall.shorewall') %}
{% elif install %}
{% do incs.append('makina-states.services.firewall.ms_iptables') %}
{% endif %}
{% if incs %}
include:
  - makina-states.services.firewall.firewall.configuration
  {% for i in incs %}
  - {{ i }}
  {% endfor %}
{% endif %}
firewall-dummy{{install}}:
  mc_proxy.hook: []
{% endmacro %}
{{ fw(install=True) }}

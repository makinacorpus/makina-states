{% import "makina-states/_macros/h.jinja" as h with context %}
{{ salt['mc_macros.register']('services', 'firewall.firewall') }}
{% macro fw(install=False)%}
{% set incs = [] %}
{% if salt['mc_services.registry']()['is'].get('firewall.firewalld') %}
{% do incs.append('makina-states.services.firewall.firewalld') %}
{% elif salt['mc_services.registry']()['is'].get('firewall.shorewall') %}
{% do incs.append('makina-states.services.firewall.shorewall') %}
{% elif install %}
{% do incs.append('makina-states.services.firewall.firewalld') %}
{% endif %}
{% if incs %}
{% macro rmacro() %}
    - watch:
      - mc_proxy: firewall-preconf
    - watch_in:
      - mc_proxy: firewall-postconf
{% endmacro %}
include:
  {% for i in incs %}
  - {{ i }}
  {% endfor %}
{% endif %}
firewall-dummy{{install}}:
  mc_proxy.hook: []
{{ h.deliver_config_files({
'/usr/bin/ms_disable_firewall.sh': {'mode': '755'}
}, after_macro=rmacro, prefix='firewall-{0}-'.format(install))}}
{% endmacro %}
{{ fw(install=True) }}

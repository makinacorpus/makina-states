{% import "makina-states/_macros/h.jinja" as h with context %}

include:
  - makina-states.services.firewall.firewall.hooks

{% macro rmacro() %}
    - watch:
      - mc_proxy: firewall-preconf
    - watch_in:
      - mc_proxy: firewall-postconf
{% endmacro %}

{{ h.deliver_config_files({
'/usr/bin/ms_disable_firewall.sh': {'mode': '755'},
}, after_macro=rmacro, prefix='firewall-')}}

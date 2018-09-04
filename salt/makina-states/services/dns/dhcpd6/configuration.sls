{% import "makina-states/_macros/h.jinja" as h with context %}
{% set settings = salt['mc_dhcpd6.settings']() %}
include:
  - makina-states.services.dns.dhcpd6.hooks
  - makina-states.services.dns.dhcpd6.services

{% macro rmacro() %}
    - watch:
      - mc_proxy: dhcpd6-pre-conf
    - watch_in:
      - mc_proxy: dhcpd6-post-conf
{% endmacro %}
{{ h.deliver_config_files(
     settings.get('templates', {}), 
     mode='750',
     user='root',
     group='root',
     after_macro=rmacro, 
     prefix='dhcpd6-')}} 

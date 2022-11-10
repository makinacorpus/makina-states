{% import "makina-states/_macros/h.jinja" as h with context %}
{% set data = salt['mc_firewalld.settings']() %}
include:
  - makina-states.services.firewall.firewalld.hooks
  - makina-states.services.firewall.firewalld.services
  - makina-states.localsettings.network
{% macro rmacro() %}
    - watch:
      - mc_proxy: firewalld-preconf
    - watch_in:
      - mc_proxy: firewalld-postconf
{% endmacro %}
{{ h.deliver_config_files(
     data.get('extra_confs', {}), after_macro=rmacro, prefix='fwld-')}}

firewalld-forward:
  sysctl.present:
    - name: net.ipv4.ip_forward
    - value: 1
    {{rmacro()}}

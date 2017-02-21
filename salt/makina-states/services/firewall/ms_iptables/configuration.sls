{% import "makina-states/_macros/h.jinja" as h with context %}
{% set data = salt['mc_ms_iptables.settings']() %}
include:
  - makina-states.services.firewall.ms_iptables.hooks
  - makina-states.services.firewall.ms_iptables.services
  - makina-states.localsettings.network
{% macro rmacro() %}
    - watch:
      - mc_proxy: ms_iptables-preconf
    - watch_in:
      - mc_proxy: ms_iptables-postconf
{% endmacro %}
{{ h.deliver_config_files(
     data.get('extra_confs', {}), after_macro=rmacro, prefix='ms_iptables-')}}

ms_iptables-forward:
  sysctl.present:
    - names:
      - net.ipv4.ip_forward
      - net.ipv6.conf.all.forwarding
    - value: 1
    {{rmacro()}}

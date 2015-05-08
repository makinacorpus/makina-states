{% import "makina-states/macros/h.jinja" as h with context %}
{# firewalld configuration#}
{%- set locs = salt['mc_locations.settings']() %}
{% set settings = salt['mc_firewalld.settings']() %}
{% set reg = salt['mc_services.registry']() %}
include:
  - makina-states.services.firewall.firewalld.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.services.firewall.firewalld.service
  - makina-states.localsettings.network

{% macro rmacro() %}
    - watch:
      - mc_proxy: firewalld-pre-conf
    - watch_in:
      - mc_proxy: firewalld-post-conf
{% endmacro %}
{{ h.deliver_config_files(data.get('extra_confs', {}),
                          after_macro=rmacro,
                          prefix='firewalld-') }}

firewalld-test-goodcfg:
  cmd.run:
    - name: firewalld check && echo "changed=false"
    - stateful: True
    - watch:
      - mc_proxy: firewalld-postconf
    - watch_in:
      - mc_proxy: firewalld-activation
{% endif %}

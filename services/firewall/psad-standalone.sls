{# Shorewall configuration
# Documentation
# - doc/ref/formulaes/services/firewall/psad.rst
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = salt['mc_localsettings.settings']()['locations'] %}
{%- set data = salt['mc_psad.settings']() %}
{{ salt['mc_macros.register']('services', 'firewall.psad') }}

{% macro do(full=True) %}
{% if full %}
psad-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - psad
    - watch_in:
      - mc_proxy: makina-psad-pre-conf
{% endif %}

makina-psad-pre-conf:
  mc_proxy.hook: []

{% for i in [
  'auto_dl',
  'icmp6_types',
  'icmp_types',
  'ip_options',
  'pf.os',
  'posf',
  'protocols',
  'psad.conf',
  'signatures',
  'snort_rule_dl',]%}
makina-etc-psad-{{i}}-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/psad/{{i}}
    - source : salt://makina-states/files/etc/psad/{{i}}
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - defaults: {{ data|yaml }}
    - watch:
      - mc_proxy: makina-psad-pre-conf
    - watch_in:
      - service: psad-service
{% endfor %}

psad-service:
  service.running:
    - name: psad
    - enable: True
{% endmacro %}
{{ do(full=False) }}

{# Shorewall configuration
# Documentation
# - doc/ref/formulaes/services/firewall/fail2ban.rst
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = salt['mc_localsettings']()['locations'] %}
{%- set data = salt['mc_fail2ban.settings']() %}
{{ salt['mc_macros.register']('services', 'firewall.fail2ban') }}

{% macro do(full=True) %}
{% if full %}
fail2ban-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - fail2ban
    - watch_in:
      - mc_proxy: makina-fail2ban-pre-conf
{% endif %}
makina-fail2ban-pre-conf:
  mc_proxy.hook: []
makina-etc-fail2ban-fail-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/fail2ban/jail.conf
    - source : salt://makina-states/files/etc/fail2ban/jail.conf
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - defaults: {{ data|yaml }}
    - watch:
      - mc_proxy: makina-fail2ban-pre-conf
    - watch_in:
      - service: fail2ban-service

makina-etc-fail2ban-fail2ban-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/fail2ban/fail2ban.conf
    - source : salt://makina-states/files/etc/fail2ban/fail2ban.conf
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - defaults: {{ data|yaml }}
    - watch:
      - mc_proxy: makina-fail2ban-pre-conf
    - watch_in:
      - service: fail2ban-service

fail2ban-service:
  service.running:
    - name: fail2ban
    - enable: True
{% endmacro %}
{{ do(full=False) }}

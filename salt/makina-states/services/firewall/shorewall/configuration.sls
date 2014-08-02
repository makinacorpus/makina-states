{# Shorewall configuration
# Documentation
# - doc/ref/formulaes/services/firewall/shorewall.rst
#}
{%- set locs = salt['mc_locations.settings']() %}
{% set settings = salt['mc_shorewall.settings']() %}
{% set reg = salt['mc_services.registry']() %}
include:
  - makina-states.services.firewall.shorewall.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.services.firewall.shorewall.services

shorewall-config:
  file.directory:
    - name: {{ locs.conf_dir }}/shorewall
    - source : salt://makina-states/files/etc/shorewall
    - template: jinja
    - user: root
    - group: root
    - watch_in:
      - mc_proxy: shorewall-preconf
    - watch_in:
      - mc_proxy: shorewall-postconf

{%- for config, cdata in settings.configs.items() %}
{% set mode = cdata.get('mode', '0700') %}
etc-shorewall-{{config}}:
  file.managed:
    - name: {{config}}
    - source : {{cdata.get('template', 'salt://makina-states/files'+config)}}
    - template: jinja
    - makedirs: {{cdata.get('makedirs', False)}}
    - user: root
    - group: root
    - mode: "{{mode}}"
    - watch_in:
      - mc_proxy: shorewall-preconf
    - watch_in:
      - mc_proxy: shorewall-postconf
{%- endfor %}
shorewall-test-cfg:
  file.exists:
    - name: {{ locs.conf_dir }}/shorewall/shorewall.conf
    - watch:
      - mc_proxy: shorewall-postconf
    - watch_in:
      - mc_proxy: shorewall-activation

shorewall-test-goodcfg-p:
  cmd.run:
    - name: shorewall check
    - require:
      - file: shorewall-test-cfg
    - require_in:
      - cmd: shorewall-test-goodcfg

shorewall-test-goodcfg:
  cmd.run:
    - name: shorewall check && echo "changed=false"
    - stateful: True
    - watch:
      - mc_proxy: shorewall-postconf
    - watch_in:
      - mc_proxy: shorewall-activation

toggle-shorewall:
  file.replace:
    - name: {{ locs.conf_dir }}/default/shorewall
    - pattern: 'startup\s*=\s*(0|1|True|False)'
    - repl: 'startup={{ settings.shw_enabled }}'
    - flags: ['MULTILINE', 'DOTALL']
    - watch:
      - mc_proxy: shorewall-activation
    - watch_in:
      - mc_proxy: shorewall-prerestart
{% endif %}

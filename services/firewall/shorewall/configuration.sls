{# Shorewall configuration
# Documentation
# - doc/ref/formulaes/services/firewall/shorewall.rst
#}
{%- set locs = salt['mc_localsettings.settings']()['locations'] %}
{% set settings = salt['mc_shorewall.settings']() %}
{% set yamled_shwdata = salt['mc_utils.json_dump'](settings) %}
{% set reg = salt['mc_services.registry']() %}
include:
  - makina-states.services.firewall.shorewall.hooks
  - makina-states.services.firewall.shorewall.service

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

{%- for config in [
  'interfaces',
  'masq',
  'params',
  'policy',
  'rules',
  'shorewall.conf',
  'zones',
] %}
etc-shorewall-{{config}}:
  file.managed:
    - name: {{ locs.conf_dir }}/shorewall/{{config}}
    - source : salt://makina-states/files/etc/shorewall/{{config}}
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - defaults:
      shwdata: |
               {{ yamled_shwdata }}
    - watch_in:
      - mc_proxy: shorewall-preconf
    - watch_in:
      - mc_proxy: shorewall-postconf
{%- endfor %}
{% set shareds = [] %}
{% if grains.get('lsb_distrib_codename') in ['wheezy'] %}
{% do shareds.extend(['macro.PostgreSQL'])%}
{% endif %}
{% for shared in shareds %}
shorewall-shared-{{shared}}:
  file.managed:
    - name: /usr/share/shorewall/{{shared}}
    - source : salt://makina-states/files/usr/share/shorewall/{{shared}}
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - defaults:
      shwdata: |
               {{ yamled_shwdata }}
    - watch_in:
      - mc_proxy: shorewall-preconf
    - watch_in:
      - mc_proxy: shorewall-postconf
{%- endfor %}


{#-
# shorewall is not managed via init scripts as we really need
# everything to be up before firewall to cut the garden off.
#}
shorewall-rc-local-d:
  file.managed:
    - name: {{ locs.conf_dir }}/rc.local.d/shorewall.sh
    - source : salt://makina-states/files/etc/rc.local.d/shorewall.sh
    - defaults:
        shwdata: |
                 {{ yamled_shwdata }}
    - mode: 0755
    - makedirs: true
    - template: jinja
    - user: root
    - group: root
    - watch_in:
      - mc_proxy: shorewall-preconf
    - watch_in:
      - mc_proxy: shorewall-postconf

shorewall-test-cfg:
  file.exists:
    - name: {{ locs.conf_dir }}/shorewall/shorewall.conf
    - watch:
      - mc_proxy: shorewall-postconf
    - watch_in:
      - mc_proxy: shorewall-activation

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

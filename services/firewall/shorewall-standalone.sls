{# Shorewall configuration
# Documentation
# - doc/ref/formulaes/services/firewall/shorewall.rst
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = salt['mc_localsettings.settings']()['locations'] %}
{% set shwdata = {'shwdata': services.shorewall} %}
{{ salt['mc_macros.register']('services', 'firewall.shorewall') }}


{% macro do(full=True) %}
{% if full %}
extend:
  toggle-shorewall:
    file.replace:
      - require_in:
        - cmd: shorewall-restart
        - file: rc-local
{% endif %}
include:
  - makina-states.localsettings.localrc
  - makina-states.services.virt.lxc-hooks
  - makina-states.services.virt.docker-hooks


{% if full %}
shorewall-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - shorewall6
      - shorewall
    - require_in:
      - file: toggle-shorewall
{% endif %}

shorewall-test-cfg:
  file.exists:
    - name: {{ locs.conf_dir }}/shorewall/shorewall.conf

shorewall-restart:
  cmd.run:
    - name: {{ locs.conf_dir }}/rc.local.d/shorewall.sh fromsalt
    - stateful: True
    - require:
      - pkg: shorewall-pkgs
    - require:
      - file: shorewall-rc-local-d
      {% if full %}
      {% if services.registry.has['virt.lxc'] %}
      - mc_proxy: lxc-post-inst
      {% endif %}
      {% if services.registry.has['virt.docker'] %}
      - mc_proxy: docker-post-inst
      {% endif %}
      - pkg: shorewall-pkgs
      {% endif %}

shorewall-config:
  file.directory:
    - name: {{ locs.conf_dir }}/shorewall
    - source : salt://makina-states/files/etc/shorewall
    - template: jinja
    - user: root
    - group: root
    - require_in:
      - file: toggle-shorewall
      - cmd: shorewall-restart

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
    - defaults: {{ shwdata }}
    - require_in:
      - file: toggle-shorewall
      - file: shorewall-config
      - cmd: shorewall-restart
{%- endfor %}

toggle-shorewall:
  file.replace:
    - name: {{ locs.conf_dir }}/default/shorewall
    - pattern: 'startup\s*=\s*(0|1|True|False)'
    - repl: 'startup={{ services.shw_enabled }}'
    - flags: ['MULTILINE', 'DOTALL']
    - require_in:
      - cmd: shorewall-restart

shorewall-e:
  service.dead:
    - names:
      - shorewall
      - shorewall6
    - enable: False
    - require_in:
      - cmd: shorewall-restart

shorewall-d:
  service.disabled:
    - names:
      - shorewall
      - shorewall6
    - require_in:
      - cmd: shorewall-restart

{#-
# shorewall is not managed via init scripts as we really need
# everything to be up before firewall to cut the garden off.
#}
shorewall-rc-local-d:
  file.managed:
    - name: {{ locs.conf_dir }}/rc.local.d/shorewall.sh
    - source : salt://makina-states/files/etc/rc.local.d/shorewall.sh
    - defaults: {{ shwdata }}
    - mode: 0755
    - makedirs: true
    - template: jinja
    - user: root
    - group: root

{#-
# Disabled as we now use {{ locs.conf_dir }}/rc.local
# shorewall-upstart:
#   file.managed:
#     - name: {{ locs.upstart_dir}}/shorewall-upstart.conf
#     - source : salt://makina-states/files/etc/init/shorewall-upstart.conf
#     - template: jinja
#     - user: root
#     - group: root
#   service.running:
#     - require:
#       - file: shorewall-upstart
#       - service: shorewall-d
#       - service: shorewall-e
#     - enable: True
#     - watch:
#       - file: shorewall-test-cfg
#}
{% endmacro %}
{{ do(full=False) }}

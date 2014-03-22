{#-
# localrc init managment
# see:
#   - makina-states/doc/ref/formulaes/localsettings/localrc.rst
#}
{% set localsettings = salt['mc_localsettings.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'localrc') }}
{%- set locs = salt['mc_localsettings.settings']()['locations'] %}
rc-local:
  file.directory:
    - name: {{ locs.conf_dir }}/rc.local.d
    - mode: 0755
    - user: root
    - group: root

rc-local-d:
  file.managed:
    - name: {{ locs.conf_dir }}/rc.local
    - source : salt://makina-states/files/etc/rc.local
    - mode: 0755
    - template: jinja
    - user: root
    - group: root
    - defaults:
      conf_dir: {{ locs.conf_dir }}

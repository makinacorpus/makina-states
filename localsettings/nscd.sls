{#-
# Base packages
# see:
#   - makina-states/doc/ref/formulaes/localsettings/nscd.rst
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.register']('localsettings', 'nscd') }}
{%- set locs = salt['mc_localsettings']()['locations'] %}
nscd-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - nscd

nscd-restart:
  cmd.run:
    - name: service nscd restart
    - require:
      - pkg: nscd-pkgs

nscd:
  service.running:
    - enable: True
    - require:
      - cmd: nscd-restart
    - watch:
      - pkg: nscd-pkgs
      - file: touch-etc-nsswitch-conf

touch-etc-nsswitch-conf:
  file.touch:
    - name: {{ locs.conf_dir }}/nsswitch.conf

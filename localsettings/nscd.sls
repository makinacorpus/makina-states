{#-
# Base packages
# see:
#   - makina-states/doc/ref/formulaes/localsettings/nscd.rst
#}
{{ salt['mc_macros.register']('localsettings', 'nscd') }}
{% if salt['mc_controllers.mastersalt_mode']() %}
{%- set locs = salt['mc_locations.settings']() %}
nscd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
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
{% endif %}

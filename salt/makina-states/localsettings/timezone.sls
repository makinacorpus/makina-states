{#-
# RVM integration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/timezone.rst
#}

{% set tzs = salt['mc_timezone.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'timezone') }}
{%- set locs = salt['mc_locations.settings']() %}
{%- set defaults = tzs %}
tz-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - tzdata
tz-conf:
  file.managed:
    - name: {{locs.conf_dir}}/timezone
    - source: salt://makina-states/files/etc/timezone
    - mode: 644
    - user: root
    - group: root
    - template: jinja

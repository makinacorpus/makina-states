{#-
# RVM integration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/timezone.rst
#}

{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.register']('localsettings', 'timezone') }}
{% macro do(full=True) %}
{%- set locs = localsettings.locations %}
{%- set defaults = localsettings.timezoneSettings %}
{% if full %}
tz-pkgs:
  pkg.installed:
    - pkgs:
      - tzdata
{% endif %}
tz-conf:
  file.managed:
    - name: {{locs.conf_dir}}/timezone
    - source: salt://makina-states/files/etc/timezone
    - mode: 644
    - user: root
    - group: root
    - template: jinja
    - defaults:
      data: {{ defaults | yaml }}

{% endmacro %}
{{ do(full=False)}}

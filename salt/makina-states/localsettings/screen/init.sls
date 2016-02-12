{#-
# screen configuration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/screen.rst
#}

{{ salt['mc_macros.register']('localsettings', 'screen') }}
{% set ugs = salt['mc_usergroup.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set settings = salt['mc_screen.settings']() %}
{% for i, p in settings.confs.items()%}
{% if not p%}{% set p = 'salt://makina-states/files'+i%}{%endif%}
screen-{{i}}:
  file.managed:
    - name: '{{i}}'
    - source: '{{p}}'
    - makedirs: true
    - mode: 755
    - user: root
    - group: root
    - template: jinja
{% endfor %}

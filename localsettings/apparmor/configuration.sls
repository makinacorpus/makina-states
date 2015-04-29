include:
  - makina-states.localsettings.apparmor.hooks
{% set settings = salt['mc_apparmor.settings']() %}

{% for f, fdata in settings.confs.items() %}
{% set template = fdata.get('template', 'jinja') %}
apparmor-conf-{{f}}:
  file.managed:
    - name: "{{fdata.get('target', f)}}"
    - source: "{{fdata.get('source', 'salt://makina-states/files'+f)}}"
    - mode: "{{fdata.get('mode', 750)}}"
    - user: "{{fdata.get('user', 'root')}}"
    - group:  "{{fdata.get('group', 'root')}}"
    {% if fdata.get('makedirs', True) %}
    - makedirs: true
    {% endif %}
    {% if template %}
    - template: "{{template}}"
    {%endif%}
    - watch:
      - mc_proxy: ms-apparmor-cfg-pre
    - watch_in:
      - mc_proxy: ms-apparmor-cfg-post
{% endfor %}

{% macro restart(suf='') %}
ms-apparmor-restart{{suf}}:
{% if settings.get('enabled', True) %}
  service.running:
    - enable: true
{%else %}
  service.dead:
    - enable: false
{%endif %}
    - name: apparmor
    - watch:
      - mc_proxy: ms-apparmor-cfg-post
    - watch_in:
      - mc_proxy: ms-apparmor-post
{% endmacro %}
{{restart()}}

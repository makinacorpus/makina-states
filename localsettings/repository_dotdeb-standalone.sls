{#-
# dotdeb.org packages repository managment
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{ salt['mc_macros.register']('localsettings', 'repository_dotdeb') }}

{{localsettings.funcs.dummy('makina-dotdeb-proxy')}}

{%- set locs = localsettings.locations %}
{%- if grains['os_family'] in ['Debian'] %}
dotdeb-repo:
  pkgrepo.managed:
    - humanname: DeadSnakes PPA
    - name: deb http://packages.dotdeb.org dotdeb all
    - dist: dotdeb
    - file: {{locs.conf_dir}}/apt/sources.list.d/dotdeb.org.list
    - keyid: E9C74FEEA2098A6E
    - keyserver: {{localsettings.keyserver }}

makina-dotdeb-pin-php:
  file.managed:
    - name: {{ locs.conf_dir }}/apt/preferences.d/dotdeb.org
    - mode: 0644
    - user: root
    - group: root
    - template: jinja
    - source: salt://makina-states/files/etc/apt/preferences.d/dotdeb.org
{% endif %}

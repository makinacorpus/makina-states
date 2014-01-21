{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{{- localsettings.register('repository_dotdeb') }}
{%- set locs = localsettings.locations %}
include:
  - {{ localsettings.statesPref }}pkgmgr

{%- if grains['os_family'] in ['Debian'] %}
makina-dotdeb-add-key:
  cmd.watch:
    - name: wget -q -O - http://www.dotdeb.org/dotdeb.gpg | sudo apt-key add -
    - unless: apt-key adv --list-keys E9C74FEEA2098A6E

makina-dotdeb-apt-update:
  cmd.run:
    - name: apt-get update
    - require:
      - cmd: makina-dotdeb-add-key
    - watch_in:
      - file: makina-dotdeb-repository
      - file: makina-dotdeb-pin-php

makina-makina-dotdeb-repository:
  file.managed:
    - name: {{ locs.conf_dir }}/apt/sources.list.d/dotdeb.org.list
    - mode: 0644
    - user: root
    - group: root
    - template: jinja
    - source: salt://makina-states/files/etc/apt/sources.list.d/dotdeb.org.list

makina-dotdeb-pin-php:
  file.managed:
    - name: {{ locs.conf_dir }}/apt/preferences.d/dotdeb.org
    - mode: 0644
    - user: root
    - group: root
    - template: jinja
    - source: salt://makina-states/files/etc/apt/preferences.d/dotdeb.org
{% endif %}

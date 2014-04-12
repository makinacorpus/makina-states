{#-
# dotdeb.org packages repository managment
#  see:
#   -  makina-states/doc/ref/formulaes/localsettings/repository_dotdeb.rst
#}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('localsettings', 'repository_dotdeb') }}
{% if full %}
include:
  - makina-states.localsettings.pkgmgr
{% endif %}
{%- set locs = salt['mc_locations.settings']() %}
{%- if grains['os_family'] in ['Debian'] %}
dotdeb-repo:
  pkgrepo.managed:
    - humanname: DotDeb PPA
    - name: deb http://packages.dotdeb.org  {{localsettings.dist}}  all
    - consolidate: true
    - dist: {{localsettings.dist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/dotdeb.org.list
    - keyid: E9C74FEEA2098A6E
    - keyserver: {{localsettings.keyserver }}
    {% if full %}
    - require:
        - file: apt-sources-list
        - cmd: apt-update-after
    {% endif %}

makina-dotdeb-pin-php:
  file.managed:
    - name: {{ locs.conf_dir }}/apt/preferences.d/dotdeb.org.pref
    - mode: 0644
    - user: root
    - group: root
    - template: jinja
    - source: salt://makina-states/files/etc/apt/preferences.d/dotdeb.org
    - require_in:
        - pkgrepo: dotdeb-repo
{% endif %}
{% endmacro %}
{{ do(full=False) }}

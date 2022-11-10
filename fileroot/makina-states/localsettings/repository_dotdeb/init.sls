{#-
# dotdeb.org packages repository managment
#  see:
#   -  makina-states/doc/ref/formulaes/localsettings/repository_dotdeb.rst
#}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'repository_dotdeb') }}
{%- if grains['os'] in ['Debian'] %}
include:
  - makina-states.localsettings.pkgs.mgr
{%- set locs = salt['mc_locations.settings']() %}
dotdeb-repo:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - humanname: DotDeb PPA
    - name: deb http://packages.dotdeb.org  {{pkgssettings.dist}}  all
    - dist: {{pkgssettings.dist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/dotdeb.org.list
    - keyid: E9C74FEEA2098A6E
    - keyserver: {{pkgssettings.keyserver }}
    - watch:
      - mc_proxy: before-pkgmgr-config-proxy
    - watch_in:
      - mc_proxy: after-base-pkgmgr-config-proxy

makina-dotdeb-pin-php:
  file.managed:
    - name: {{ locs.conf_dir }}/apt/preferences.d/dotdeb.org.pref
    - mode: 0644
    - user: root
    - group: root
    - template: jinja
    - source: salt://makina-states/files/etc/apt/preferences.d/dotdeb.org
    - watch_in:
        - pkgrepo: dotdeb-repo
{% else %}
no-op: {mc_proxy.hook: []}
{% endif %}

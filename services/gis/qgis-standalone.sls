{{ salt['mc_macros.register']('services', 'gis.qgis') }}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set locs = salt['mc_locations.settings']() %}
{% macro do(full=True) %}
{# its up to the project to decide the fcgi implementation afterall
include:
  {% if full %}
  - makina-states.services.http.apache_modfastcgi
  {% else %}
  - makina-states.services.http.apache_modfastcgi-standalone
  {% endif %}
#}

{% if full %}
{% import "makina-states/services/php/common.sls" as phpcommon with context %}
{% if grains['os_family'] in ['Debian'] %}
qgis-repo:
  pkgrepo.managed:
    - name: deb http://qgis.org/debian {{localsettings.dist}} main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/qgis.list
    - keyid: '47765B75'
    - keyserver: {{localsettings.keyserver }}

prereq-qgis:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - require:
      - pkgrepo: qgis-repo
    - pkgs:
      - qgis-mapserver
      - curl
      - {{salt['mc_php.settings']().packages['curl'] }}
      - {{salt['mc_php.settings']().packages['sqlite'] }}
      - {{salt['mc_php.settings']().packages['gd'] }}
      - {{salt['mc_php.settings']().packages['postgresql'] }}
      {# deps #}
      - autoconf
      - automake
      - build-essential
      - bzip2
      - gettext
      - git
      - groff
      - libbz2-dev
      - libcurl4-openssl-dev
      - libdb-dev
      - libgdbm-dev
      - libjpeg62-dev
      - libreadline-dev
      - libsigc++-2.0-dev
      - libsqlite0-dev
      - libsqlite3-dev
      - libssl-dev
      - libtool
      - libxml2-dev
      - libxslt1-dev
      - m4
      - man-db
      - pkg-config
      - poppler-utils
      - python-dev
      - python-imaging
      - python-setuptools
      - tcl8.4
      - tcl8.4-dev
      - tcl8.5
      - tcl8.5-dev
      - tk8.5-dev
      - wv
      - zlib1g-dev
{% endif %}
{% endif %}
{%- endmacro %}
{{ do(full=False) }}

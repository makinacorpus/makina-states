{% import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'gis.qgis') }}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}

include:
  - makina-states.services.gis.postgis

{% if grains['os_family'] in ['Debian'] %}
qgis-repo:
  pkgrepo.managed:
    - name: deb http://qgis.org/debian {{localsettings.dist}} main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/qgis.list
    - keyid: '47765B75'
    - keyserver: {{localsettings.keyserver }}

prereq-qgis:
  pkg.installed:
    - require:
      - pkgrepo: qgis-repo
    - pkgs:
      - qgis-mapserver
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
      - libapache2-mod-fcgid
{% endif %}

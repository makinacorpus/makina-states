{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% if grains['os_family'] in ['Debian'] %}
include:
  - makina-states.services.gis.ubuntugis
{% set locs = salt['mc_locations.settings']() %}
qgis-repo:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - name: deb http://qgis.org/debian {{pkgssettings.dist}} main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/qgis.list
    - keyid: '47765B75'
    - keyserver: {{pkgssettings.keyserver }}
    - require:
      - cmd: qgis-repo
  cmd.run:
    - name: sudo apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 030561BEDD45F6C3
    - unless: apt-key list|grep -q DD45F6C3
qgis-repo-ubuntu:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - name: deb http://qgis.org/ubuntugis {{pkgssettings.dist}} main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/qgisubuntugis.list
    - keyid: '47765B75'
    - keyserver: {{pkgssettings.keyserver }}
    - require:
      - cmd: qgis-repo
  cmd.run:
    - name: sudo apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 030561BEDD45F6C3
    - unless: apt-key list|grep -q 618E5811

prereq-qgis:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - require:
      - pkgrepo: qgis-repo
      - mc_proxy: ubuntugis-post-install-hook
    - pkgs:
      - qgis-server
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

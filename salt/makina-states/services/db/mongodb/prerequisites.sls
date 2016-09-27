{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set mongodbSettings = salt['mc_mongodb.settings']() %}
include:
  - makina-states.services.db.mongodb.hooks

{% set dist = pkgssettings.udist %}
{% if grains['os'] in ['Debian'] %}
{% set mir = 'deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen' %}
{% endif %}
mongodb-base:
  pkgrepo.managed:
    - humanname: mongodb ppa
    - name: {{mir}}
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/mongodb.list
    - keyid: 7F0CEB10
    - keyserver: keyserver.ubuntu.com
    - require_in:
      - pkg: mongodb-pkgs

mongodb-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - mongodb-org
      - python-pymongo
    - watch:
      - mc_proxy: mongodb-pre-install
    - watch_in:
      - mc_proxy: mongodb-pre-hardrestart
      - mc_proxy: mongodb-post-install


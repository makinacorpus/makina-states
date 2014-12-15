{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set redisSettings = salt['mc_redis.settings']() %}
include:
  - makina-states.services.db.redis.hooks

{% if grains['os_family'] in ['Debian'] %}
{% set dist = pkgssettings.udist %}
{% endif %}
{% if grains['os'] in ['Debian'] %}
{% set dist = pkgssettings.ubuntu_lts %}
{% set mir = 'deb http://downloads-distro.redis.org/repo/debian-sysvinit dist 10gen' %}
{% else %}
{% set mir = 'deb http://downloads-distro.redis.org/repo/debian-sysvinit dist 10gen' %}
{% endif %}
redis-base:
  pkgrepo.managed:
    - humanname: redis ppa
    - name: {{mir}}
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/redis.list
    - keyid: 7F0CEB10
    - keyserver: keyserver.ubuntu.com
    - require_in:
      - pkg: redis-pkgs

redis-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - redis-org
      - python-pyredis
    - watch:
      - mc_proxy: redis-pre-install
    - watch_in:
      - mc_proxy: redis-pre-hardrestart
      - mc_proxy: redis-post-install


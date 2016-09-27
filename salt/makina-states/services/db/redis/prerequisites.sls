{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set redisSettings = salt['mc_redis.settings']() %}
include:
  - makina-states.services.db.redis.hooks
{% set dist = pkgssettings.udist %} 
{% set mir = 'deb http://ppa.launchpad.net/chris-lea/redis-server/ubuntu {0} main'.format(dist) %}
redis-base:
  pkgrepo.managed:
    - humanname: redis ppa
    - name: {{mir}}
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/redis.list
    - keyid: C7917B12
    - keyserver: keyserver.ubuntu.com
    - require_in:
      - pkg: redis-pkgs

redis-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{redisSettings.packages}}
    - watch:
      - mc_proxy: redis-pre-install
    - watch_in:
      - mc_proxy: redis-pre-hardrestart
      - mc_proxy: redis-post-install


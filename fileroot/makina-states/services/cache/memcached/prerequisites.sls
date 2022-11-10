{% set settings = salt['mc_memcached.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.cache.memcached.hooks
memcached-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.pkgs}}
    - watch:
      - mc_proxy: memcached-pre-install
    - watch_in:
      - mc_proxy: memcached-post-install

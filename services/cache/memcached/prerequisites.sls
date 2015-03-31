{% set settings = salt['mc_memcached.settings']() %}
{% set salts = salt['mc_salt.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.cache.memcached.hooks
  - makina-states.controllers.hooks
memcached-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.pkgs}}
    - watch:
      - mc_proxy: memcached-pre-install
    - watch_in:
      - mc_proxy: memcached-post-install

{% for i in ['salt', 'mastersalt'] %}
{% set p = salts['data_mappings']['common'][i]['venv_path']%}
{% set pip = p + '/bin/pip' %}
{{i}}-memcached-py:
  pip.installed:
    - name: pylibmc
    - bin_env: "{{p}}"
    - onlyif: test -e "{{pip}}"
    - watch:
      - mc_proxy: memcached-pre-install
      - pkg: memcached-pkgs
    - watch_in:
      - mc_proxy: memcached-post-install
      - mc_proxy: dummy-pre-mastersalt-service-restart
{%endfor%}

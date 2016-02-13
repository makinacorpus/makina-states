{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_memcached.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}
{% if not salt['mc_nodetypes.is_docker']() %}
memcached-service-restart:
  service.running:
    - name: {{settings.service_name}}
    - enable: True
    - watch:
      - mc_proxy: memcached-pre-restart
    - watch_in:
      - mc_proxy: memcached-post-restart
{% endif %}

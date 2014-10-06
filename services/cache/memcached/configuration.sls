{% set settings = salt['mc_memcached.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}
{% if salt['mc_controllers.mastersalt_mode']() %}
include:
  - makina-states.services.cache.memcached.hooks
  - makina-states.services.cache.memcached.services
{% for file, tp in settings.templates.items() %}
memcached_config_{{tp}}:
  file.managed:
    - name: {{file}}
    - makedirs: true
    - source: {{tp}}
    - template: jinja
    - mode: 750
    - user: root
    - group: root
    - defaults:
      data: |
            {{yameld_data}}
    - watch:
      - mc_proxy: memcached-pre-conf
    - watch_in:
      - mc_proxy: memcached-post-conf
{% endfor %}
{% endif%}

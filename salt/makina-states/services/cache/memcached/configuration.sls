{% set settings = salt['mc_memcached.settings']() %}
{% if salt['mc_controllers.allow_lowlevel_states']() %}
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
    - watch:
      - mc_proxy: memcached-pre-conf
    - watch_in:
      - mc_proxy: memcached-post-conf
{% endfor %}
{% endif%}

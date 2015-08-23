{% import "makina-states/_macros/h.jinja" as h with context %}
{% set data = salt['mc_redis.settings']() %}
include:
  - makina-states.services.db.redis.hooks
  - makina-states.services.db.redis.services

{% macro rmacro() %}
    - watch:
      - mc_proxy: redis-pre-conf
    - watch_in:
      - mc_proxy: redis-post-conf
{% endmacro %}

{{ h.deliver_config_files(
     data.templates,
     user='redis',
     group='redis',
     after_macro=rmacro,
     prefix='makina-redis-')}}

makina-redis-localconf:
  file.managed:
    - name: /etc/redis/redis.local.conf
    - user: redis
    - group: redis
    - mode: 750
    - makedirs: true
    - source: ''
    - watch:
      - mc_proxy: redis-pre-conf
    - watch_in:
      - mc_proxy: redis-post-conf

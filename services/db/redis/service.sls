{% set redisSettings = salt['mc_redis.settings']() %}
include:
  - makina-states.services.db.redis.hooks

makina-redis-service:
  service.running:
    - name: {{redisSettings.service}}
    - enable: true
    {# does not work - reload: true #}
    - watch:
      - mc_proxy: redis-pre-restart
    - watch_in:
      - mc_proxy: redis-post-restart

makina-redis-restart-service:
  service.running:
    - name: {{redisSettings.service}}
    - enable: true
    - watch:
      - mc_proxy: redis-pre-hardrestart
    - watch_in:
      - mc_proxy: redis-post-hardrestart


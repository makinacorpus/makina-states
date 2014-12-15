include:
  - makina-states.services.db.redis.hooks

makina-redis-service:
  service.running:
    - name: redisd
    - enable: true
    - reload: true
    - watch:
      - mc_proxy: redis-pre-restart
    - watch_in:
      - mc_proxy: redis-post-restart

makina-redis-restart-service:
  service.running:
    - name: redisd
    - enable: true
    - watch:
      - mc_proxy: redis-pre-hardrestart
    - watch_in:
      - mc_proxy: redis-post-hardrestart


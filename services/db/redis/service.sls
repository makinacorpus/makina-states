{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% set redisSettings = salt['mc_redis.settings']() %}
include:
  - makina-states.services.db.redis.hooks
{% if salt['mc_nodetypes.is_docker']() %}
  - makina-states.services.monitoring.circus.hooks

{% set circus_data = {
  'cmd': '/usr/bin/redis-server /etc/redis.conf',
  'environment': {},
  'uid': 'redis',
  'gid': 'redis',
  'copy_env': True,
  'working_dir': '/',
  'warmup_delay': "10",
  'max_age': 24*60*60} %}
{{ circus.circusAddWatcher('makina-states-redis', **circus_data) }}

{%else %}
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
{% endif %}

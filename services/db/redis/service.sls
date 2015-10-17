{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% set redisSettings = salt['mc_redis.settings']() %}
include:
  - makina-states.services.db.redis.hooks
  {% if salt['mc_nodetypes.is_docker_service']() %}
  - makina-states.services.monitoring.circus.hooks
  {% endif %}

{% if salt['mc_nodetypes.is_docker_service']() %}
{% set circus_data = {
  'cmd': '/usr/bin/redis-server-wrapper.sh /etc/redis/redis.conf',
  'environment': {},
  'uid': 'root',
  'gid': 'redis',
  'rlimit_nofile': '65536',
  'copy_env': True,
  'working_dir': '/',
  'warmup_delay': "3",
  'conf_priority': '50',
  'max_age': 24*60*60} %}
{{ circus.circusAddWatcher('redis', **circus_data) }}
{%else %}
{% if not salt['mc_nodetypes.is_docker']() %}
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
{%endif%}
{% endif %}

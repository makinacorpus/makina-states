{%- import "makina-states/_macros/h.jinja" as h with context %}
{%- set redisSettings = salt['mc_redis.settings']() %}
{%- set pm = salt['mc_services_managers.get_processes_manager'](redisSettings) %}
{%- set service_function = salt['mc_services_managers.get_service_function'](pm) %}
include:
  - makina-states.services.db.redis.hooks
  {% if salt['mc_nodetypes.is_docker_service']() %}
  - makina-states.services.monitoring.circus.hooks
  {% endif %}
  {% if pm in salt['mc_services_managers.processes_managers']() %}
  - makina-states.services_managers.{{pm}}.hooks
  {% endif %}

{% if pm == 'circus' %}
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
{% endif %}

{% if service_function %}
{% macro reload_macro() %}
    - watch:
      - mc_proxy: redis-pre-restart
    - watch_in:
      - mc_proxy: redis-post-restart
{% endmacro %}
{% macro restart_macro() %}
    - watch:
      - mc_proxy: redis-pre-hardrestart
    - watch_in:
      - mc_proxy: redis-post-hardrestart
{% endmacro %}
{{ h.service_restart_reload(redisSettings.service,
                            service_function=service_function,
                            pref='makina-redis',
                            restart_macro=restart_macro,
                            reload_macro=reload_macro) }}
{% endif %}

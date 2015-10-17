{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
include:
  - makina-states.services.base.cron.hooks
  {% if salt['mc_nodetypes.is_docker_service']() %}
  - makina-states.services.monitoring.circus.hooks
  {% endif %}

{% if salt['mc_nodetypes.activate_sysadmin_states']() %}
{% if not salt['mc_nodetypes.is_docker_service']() %}
{% if not salt['mc_nodetypes.is_docker']() %}
makina-cron-service:
  service.running:
    - name: cron
    - enable: true
    - watch:
      - mc_proxy: cron-prerestart
    - watch_in:
      - mc_proxy: cron-postrestart

makina-cron-restart-service:
  service.running:
    - name: cron
    - enable: true
    - watch:
      - mc_proxy: cron-prehardrestart
    - watch_in:
      - mc_proxy: cron-posthardrestart
{% endif %}
{% else %}
{% set circus_data = {
  'cmd': '/usr/sbin/cron -f',
  'environment': {},
  'uid': 'root',
  'gid': 'root',
  'copy_env': True,
  'stop_signal': 'INT',
  'conf_priority': '11',
  'working_dir': '/',
  'warmup_delay': "1",
  'max_age': 24*60*60} %}
{{ circus.circusAddWatcher('cron', **circus_data) }}
{% endif %}
{% endif %}

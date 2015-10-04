{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
include:
  - makina-states.services.base.cron.hooks
  {% if salt['mc_nodetypes.is_docker']() %}
  - makina-states.services.monitoring.circus.hooks
  {% endif %} 
{% if salt['mc_controllers.mastersalt_mode']() and not salt['mc_nodetypes.is_container']() %}
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
{% if salt['mc_nodetypes.is_docker']() and not salt['mc_controllers.mastersalt_mode']()%}
{% set circus_data = {
  'cmd': '/usr/sbin/cron -f',
  'environment': {},
  'uid': 'root',
  'gid': 'root',
  'copy_env': True,
  'stop_signal': 'INT',
  'working_dir': '/',
  'warmup_delay': "10",
  'max_age': 24*60*60} %}
{{ circus.circusAddWatcher('makina-states-cron', **circus_data) }}
{% endif %}

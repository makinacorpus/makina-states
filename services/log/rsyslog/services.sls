{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
include:
  - makina-states.services.log.rsyslog.hooks
  {% if salt['mc_nodetypes.is_docker']() %}
  - makina-states.services.monitoring.circus.hooks
  {% endif %}
{% if salt['mc_controllers.mastersalt_mode']() %}
makina-rsyslog-restart-service:
  service.running:
    - name: rsyslog
    - enable: true
    - watch:
      - mc_proxy: rsyslog-pre-restart-hook
      - mc_proxy: rsyslog-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: rsyslog-post-restart-hook
      - mc_proxy: rsyslog-post-hardrestart-hook
{% endif %}
{% if salt['mc_nodetypes.is_docker']() and not salt['mc_controllers.mastersalt_mode']()%}
{% set circus_data = {
  'cmd': '/usr/sbin/rsyslogd -n',
  'environment': {},
  'uid': 'root',
  'gid': 'root',
  'copy_env': True,
  'rlimit_nofile': '4096',
  'working_dir': '/var',
  'warmup_delay': "10",
  'max_age': 24*60*60} %}
{{ circus.circusAddWatcher('makina-states-rsyslogd', **circus_data) }}
{%endif%}

{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
include:
  - makina-states.services.log.rsyslog.hooks
  {% if salt['mc_nodetypes.is_docker_service']()%}
  - makina-states.services.monitoring.circus.hooks
  {% endif %}
{% if not salt['mc_nodetypes.is_docker_service']() %}
{% if not salt['mc_nodetypes.is_docker']() %}
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
{%endif%}
{% else %}
{% set circus_data = {
  'cmd': '/usr/sbin/rsyslogd -n',
  'environment': {},
  'uid': 'root',
  'gid': 'root',
  'stop_signal': 'INT',
  'conf_priority': '11',
  'copy_env': True,
  'rlimit_nofile': '4096',
  'working_dir': '/var',
  'warmup_delay': "1",
  'max_age': 24*60*60} %}
{{ circus.circusAddWatcher('rsyslogd', **circus_data) }}
{%endif%}

{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
include:
  - makina-states.services.firewall.fail2ban.hooks
  {% if salt['mc_nodetypes.is_docker_service']() %}
  - makina-states.services.monitoring.circus.hooks
  {%endif %}
{% if not salt['mc_nodetypes.is_docker_service']() %}
{% if not salt['mc_nodetypes.is_docker']() %}
fail2ban-service:
  service.running:
    - name: fail2ban
    - enable: True
    - watch:
      - mc_proxy: fail2ban-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: fail2ban-post-hardrestart-hook
{% endif %}
{% else %}
{% set circus_data = {
  'cmd': '/usr/bin/fail2ban-server -s /var/run/fail2ban/fail2ban.sock -p /var/run/fail2ban/fail2ban.pid -x -f',
  'environment': {},
  'uid': 'root',
  'gid': 'root',
  'copy_env': True,
  'conf_priority': '11',
  'stop_signal': 'INT',
  'working_dir': '/',
  'warmup_delay': "2",
  'max_age': 31*24*60*60} %}
{{ circus.circusAddWatcher('fail2ban', **circus_data) }}
{% endif %}

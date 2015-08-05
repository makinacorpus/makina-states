{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% import "makina-states/services/monitoring/supervisor/macros.jinja" as supervisor with context %}
{% set openssh = salt['mc_ssh.settings']() %}
{% set pm = salt['mc_services.get_processes_manager'](openssh) %}
include:
  - makina-states.services.base.ssh.hooks
  {% if pm in ['circus', 'supervisor'] %}
  - makina-states.services.monitoring.{{pm}}.hooks
  {% endif %}
{% if salt['mc_nodetypes.activate_sysadmin_states']() %}
{% set toggle_service = salt['mc_services.toggle_service'](pm) %}
{% if toggle_service %}
openssh-svc:
  service.{{toggle_service}}:
    - name: {{openssh.service}}
    - enable: {{salt['mc_services.toggle_enable'](toggle_service)}}
    - watch:
      - mc_proxy: ssh-service-prerestart
    - watch_in:
      {% if pm != 'system' %}- mc_proxy: {{pm}}-pre-restart{%endif%}
      - mc_proxy: ssh-service-postrestart
{% endif %}
{% if pm == 'circus' %}
{% set circus_data = {
  'cmd': '/usr/bin/sshd_wrapper.sh -D',
  'environment': {},
  'uid': 'root',
  'gid': 'root',
  'copy_env': True,
  'stop_signal': 'INT',
  'conf_priority': '11',
  'working_dir': '/',
  'warmup_delay': "4"} %}
{{ circus.circusAddWatcher('ssh', **circus_data) }}
{% if pm == 'supervisor' %}
{% set supervisor_data = {
  'command': '/usr/bin/sshd_wrapper.sh -D',
  'user': 'root',
  'stopsignal': 'INT',
  'conf_priority': '11',
  'directory': '/',
  'startsecs': "4"} %}
{{ supervisor.supervisorAddProgram('ssh', **supervisor_data) }}
{% endif %}
{% endif %}
{% endif %}

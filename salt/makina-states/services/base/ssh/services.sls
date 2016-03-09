{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% import "makina-states/services/monitoring/supervisor/macros.jinja" as supervisor with context %}
{% set settings = salt['mc_ssh.settings']() %}
{% set pm = salt['mc_services_managers.get_processes_manager'](settings) %}
{% set service_function = salt['mc_services_managers.get_service_function'](pm) %}
include:
  - makina-states.services.base.ssh.hooks
  {% if pm in salt['mc_services_managers.processes_managers']() %}
  - makina-states.services_managers.{{pm}}.hooks
  {% endif %}
{% if service_function %}
openssh-svc:
  {{service_function}}:
    - name: {{settings.service}}
    - reload: true
    - enable: {{salt['mc_services_managers.get_service_enabled_state'](service_function)}}
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
  'send_hup': 'true',
  'conf_priority': '11',
  'working_dir': '/',
  'warmup_delay': "4"} %}
{{ circus.circusAddWatcher('ssh', **circus_data) }}
{% endif %}

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

{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% set openssh = salt['mc_ssh.settings']() %}
include:
  - makina-states.services.base.ssh.hooks
  {% if salt['mc_nodetypes.is_docker_service']() %}
  - makina-states.services.monitoring.circus.hooks
  {%endif %}
{% if salt['mc_nodetypes.activate_sysadmin_states']() %}
{% if not salt['mc_nodetypes.is_docker_service']() %}
openssh-svc:
  service.running:
    - watch_in:
      - mc_proxy: ssh-service-prerestart
    - watch_in:
      - mc_proxy: ssh-service-postrestart
    - enable: True
    {%- if grains['os_family'] == 'Debian' %}
    - name: ssh
    {% else %}
    - name: sshd
    {%- endif %}
{% else %}
{% set circus_data = {
  'cmd': '/usr/bin/sshd_wrapper.sh -D',
  'environment': {},
  'uid': 'root',
  'gid': 'root',
  'copy_env': True,
  'stop_signal': 'INT',
  'conf_priority': '11',
  'working_dir': '/',
  'warmup_delay': "4",
  'max_age': 31*24*60*60} %}
{{ circus.circusAddWatcher('ssh', **circus_data) }}
{% endif %}
{% endif %}

{% set settings = salt['mc_haproxy.settings']() %}
{% set pm = salt['mc_services_managers.get_processes_manager'](settings) %}
{% set service_function = salt['mc_services_managers.get_service_function'](pm) %}
include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.localsettings.ssl.hooks
  {% if pm in salt['mc_services_managers.processes_managers']() %}
  - makina-states.services_managers.{{pm}}.hooks
  {% endif %}

{% if service_function %}
makina-haproxy-service:
  {{service_function}}:
    - name: haproxy
    - enable: {{salt['mc_services_managers.get_service_enabled_state'](service_function)}}
    - reload: true
    - watch:
      - mc_proxy: haproxy-pre-restart-hook
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: haproxy-post-restart-hook

makina-haproxy-restart-service:
  {{service_function}}:
    - name: haproxy
    - enable: {{salt['mc_services_managers.get_service_enabled_state'](service_function)}}
    - watch:
      - mc_proxy: haproxy-pre-hardrestart-hook
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: haproxy-post-hardrestart-hook
{% endif %}

{% if pm == 'circus' %}
{% set circus_data = {
  'cmd': '/usr/bin/mc_haproxy.sh start',
  'environment': {},
  'uid': 'root',
  'gid': 'root',
  'stop_signal': 'INT',
  'hup_signal': 'USR2',
  'copy_env': True,
  'send_hup': True,
  'rlimit_nofile': '4096',
  'conf_priority': '60',
  'working_dir': '/var/www/html',
  'warmup_delay': "2"} %}
{{ circus.circusAddWatcher('haproxy', **circus_data) }}
{% endif %}

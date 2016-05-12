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
    - onfail_in:
      - cmd: fail-makina-haproxy-service
      - "{{service_function.split('.')[0]}}": fail-makina-haproxy-service

makina-haproxy-restart-service:
  {{service_function}}:
    - name: haproxy
    - enable: {{salt['mc_services_managers.get_service_enabled_state'](service_function)}}
    - watch:
      - mc_proxy: haproxy-pre-hardrestart-hook
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: haproxy-post-hardrestart-hook
    - onfail_in:
      - cmd: fail-makina-haproxy-restart-service
      - "{{service_function.split('.')[0]}}": fail-makina-haproxy-restart-service

{% macro systemd_reload() %}
    - name: systemctl daemon-reload
    - onlyif: systemctl show haproxy
{% endmacro %}

fail-makina-haproxy-service:
  cmd.run:
    {{systemd_reload()}}
    - watch:
      - mc_proxy: haproxy-pre-restart-hook
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: haproxy-post-restart-hook
  {{service_function}}:
    - name: haproxy
    - enable: {{salt['mc_services_managers.get_service_enabled_state'](service_function)}}
    - reload: true
    - watch:
      - cmd: fail-makina-haproxy-service
      - mc_proxy: haproxy-pre-restart-hook
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: haproxy-post-restart-hook

fail-makina-haproxy-restart-service:
  cmd.run:
    {{systemd_reload()}}
    - watch:
      - mc_proxy: haproxy-pre-hardrestart-hook
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: haproxy-post-hardrestart-hook
  {{service_function}}:
    - name: haproxy
    - enable: {{salt['mc_services_managers.get_service_enabled_state'](service_function)}}
    - watch:
      - cmd: fail-makina-haproxy-restart-service
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

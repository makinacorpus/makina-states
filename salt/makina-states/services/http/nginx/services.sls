{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% set settings = salt['mc_nginx.settings']() %}
{% set pm = salt['mc_services_managers.get_processes_manager'](settings) %}
{% set service_function = salt['mc_services_managers.get_service_function'](pm) %}
include:
  - makina-states.services.http.nginx.hooks
  {% if pm in salt['mc_services_managers.processes_managers']() %}
  - makina-states.services_managers.{{pm}}.hooks
  {% endif %}
  - makina-states.services_managers.circus.hooks

{# Configuration checker, always run before restart of graceful restart #}
makina-nginx-conf-syntax-check:
  cmd.run:
    - name: {{ salt['mc_salt.settings']().msr }}/files/usr/bin/nginxConfCheck.sh
    - stateful: True
    - watch_in:
      - mc_proxy: nginx-pre-restart-hook
    - watch:
      - mc_proxy: nginx-post-conf-hook


{#
 # sometimes the pid file exists but is empty somehow
 # calling stop nginx will kill any running nginx services
 # and we ensure to remove the pidfile after
 #
 ##}
makina-nginx-safebelt-restart:
  cmd.run:
    - name: |
            set -x
            p="/var/run/nginx.pid"
            if [ -e "$p" ];then
              if [ "x$(cat $p)" = "x" ];then
                service nginx stop || /bin/true
                rm -f "${p}" || /bin/true
              fi
            fi
            echo changed=false
    - stateful: true
    - watch:
      - mc_proxy: nginx-post-conf-hook
    - watch_in:
      - mc_proxy: nginx-pre-hardrestart-hook
      - mc_proxy: nginx-pre-restart-hook

{% if service_function %}
makina-nginx-restart:
  {{service_function}}:
    - names: [{{ settings.service }}]
    - enable: {{salt['mc_services_managers.get_service_enabled_state'](service_function)}}
    - reload: true
    - watch:
      - cmd: makina-nginx-safebelt-restart
      - mc_proxy: nginx-pre-restart-hook
    - watch_in:
      - mc_proxy: nginx-post-restart-hook

makina-nginx-hard-restart:
  {{service_function}}:
    - names: [{{ settings.service }}]
    - enable: {{salt['mc_services_managers.get_service_enabled_state'](service_function)}}
    - watch:
      - cmd: makina-nginx-safebelt-restart
      - mc_proxy: nginx-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: nginx-post-hardrestart-hook
{% endif %}

{% set circus_data = {
  'cmd': "/usr/sbin/nginx -g 'daemon off;master_process on;'",
  'environment': {},
  'uid': 'root',
  'gid': 'root',
  'stop_signal': 'INT',
  'copy_env': True,
  'send_hup': True,
  'rlimit_nofile': '4096',
  'conf_priority': '60',
  'working_dir': '/var/www/html',
  'warmup_delay': "2"} %}
{{ circus.circusToggleWatcher(pm=='circus', 'nginx', **circus_data) }}

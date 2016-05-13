{%- import "makina-states/_macros/h.jinja" as h with context %}
{%- set settings = salt['mc_haproxy.settings']() %}
{%- set pm = salt['mc_services_managers.get_processes_manager'](settings) %}
{%- set service_function = salt['mc_services_managers.get_service_function'](pm) %}
include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.localsettings.ssl.hooks
  {% if pm in salt['mc_services_managers.processes_managers']() %}
  - makina-states.services_managers.{{pm}}.hooks
  {% endif %}

{% macro restart_macro() %}
    - watch:
      - mc_proxy: haproxy-pre-restart-hook
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: haproxy-post-restart-hook

{% endmacro%}
{% macro reload_macro() %}
    - watch:
      - mc_proxy: haproxy-pre-hardrestart-hook
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: haproxy-post-hardrestart-hook
{% endmacro%}
{{ h.service_restart_reload('haproxy',
                            service_function=service_function,
                            pref='makina-haproxy',
                            restart_macro=restart_macro,
                            reload_macro=reload_macro) }}
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

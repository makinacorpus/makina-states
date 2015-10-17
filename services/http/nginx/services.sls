{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
include:
  - makina-states.services.http.nginx.hooks
  {% if salt['mc_nodetypes.is_docker_service']() %}
  - makina-states.services.monitoring.circus.hooks
  {% endif %}


#--- MAIN SERVICE RESTART/RELOAD requireers --------------
# Configuration checker, always run before restart of graceful restart
{% set settings = salt['mc_nginx.settings']() %}
makina-nginx-conf-syntax-check:
  cmd.run:
    - name: {{ salt['mc_salt.settings']().msr }}/_scripts/nginxConfCheck.sh
    - stateful: True
    - watch:
      - mc_proxy: nginx-pre-restart-hook
      - mc_proxy: nginx-pre-hardrestart-hook
{% if not salt['mc_nodetypes.is_docker']() %}
    - watch_in:
      - service: makina-nginx-restart
      - service: makina-nginx-reload
{% endif %}

{% if salt['mc_nodetypes.is_docker_service']()%}
{% set circus_data = {
  'cmd': '/usr/sbin/nginx',
  'environment': {},
  'uid': 'root',
  'gid': 'root',
  'stop_signal': 'INT',
  'copy_env': True,
  'rlimit_nofile': '4096',
  'conf_priority': '60',
  'working_dir': '/var/www/html',
  'warmup_delay': "2",
  'max_age': 24*60*60} %}
{{ circus.circusAddWatcher('nginx', **circus_data) }}
{% else %}
{% if not salt['mc_nodetypes.is_docker']() %}
{# compat: reload #}
{% for i in ['reload', 'restart'] %}
makina-nginx-{{i}}:
  service.running:
    - name: {{ settings.service }}
    - enable: True
    - watch_in:
      - mc_proxy: nginx-post-restart-hook
      - mc_proxy: nginx-post-hardrestart-hook
    - watch:
      - mc_proxy: nginx-pre-restart-hook
      - mc_proxy: nginx-pre-hardrestart-hook
{%endif %}
{% endfor %}

makina-ngin-naxsi-ui-running:
{# totally disable naxui for now #}
{% if False %}
  service.running:
    - enable: True
{% else %}
  service.dead:
    - enable: False
{% endif %}
    - name: nginx-naxsi-ui
    - require_in:
      - mc_proxy: nginx-post-restart-hook
    - require:
      - mc_proxy: nginx-pre-restart-hook
{% endif %}

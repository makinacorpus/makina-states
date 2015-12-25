{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}
{% import "makina-states/services/http/nginx/services.sls" as services %}
include:
  - makina-states.services_managers.circus.hooks
  - makina-states.services.http.nginx.hooks
  - makina-states.services.http.nginx.unregister
{% set settings = salt['mc_nginx.settings']() %}
{% set pm = salt['mc_services_managers.get_processes_manager'](settings) %}
{% set service_function = salt['mc_services_managers.get_service_function'](pm) %}
{% if service_function %}
makina-nginx-disable:
  service.dead:
    - names: [{{ settings.service }}]
    - enable: false
    - watch:
      - mc_proxy: nginx-pre-restart-hook
    - watch_in:
      - mc_proxy: nginx-post-restart-hook
      - pkg: nginx-purge-nginx
{% endif %}
{{ circus.circusToggleWatcher(False, 'nginx', **services.circus_data) }}
nginx-disable-makinastates-nginx:
  file.absent:
    - names:
      - /etc/apt/sources.list.d/nginx.list
    - watch:
      - mc_proxy: nginx-pre-restart-hook
      - mc_proxy: nginx-pre-disable
    - watch_in:
      - mc_proxy: nginx-post-disable
nginx-purge-nginx:
  pkg.purged:
    - pkgs: [nginx, nginx-full, nginx-extras, nginx-common]
    - watch:
      - file: nginx-disable-makinastates-nginx
      - mc_proxy: nginx-pre-disable
    - watch_in:
      - mc_proxy: nginx-post-disable
nginx-cleanup-makinastates-nginx:
  file.absent:
    - names:
      - /etc/nginx
      - /etc/default/nginx
      - /etc/logrotate.d/nginx
      - /etc/init.d/nginx
    - watch:
      - mc_proxy: nginx-pre-disable
    - watch_in:
      - mc_proxy: nginx-post-disable

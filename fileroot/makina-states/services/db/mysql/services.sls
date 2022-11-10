{%- import "makina-states/_macros/h.jinja" as h with context %}
{%- set mysqlData = salt['mc_mysql.settings']() %}
{%- set pm = salt['mc_services_managers.get_processes_manager'](mysqlData) %}
{%- set service_function = salt['mc_services_managers.get_service_function'](pm) %}
include:
  - makina-states.services.db.mysql.hooks
  - makina-states.services.db.mysql.checkroot
  - makina-states.localsettings.ssl.hooks
  {% if pm in salt['mc_services_managers.processes_managers']() %}
  - makina-states.services_managers.{{pm}}.hooks
  {% endif %}

{% if service_function %}
{% macro restart_macro() %}
    - watch:
      - mc_proxy: mysql-pre-hardrestart-hook
      - mc_proxy: ssl-certs-end
    - watch_in:
      - mc_proxy: mysql-post-hardrestart-hook
      - mc_proxy: makina-mysql-service-reload-r
{% endmacro %}
{% macro reload_macro() %}
    - require:
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: ssl-certs-end
    - require_in:
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: makina-mysql-service-reload-r
{% endmacro %}
{{ h.service_restart_reload(mysqlData.service,
                            service_function=service_function,
                            pref='makina-mysql',
                            restart_macro=restart_macro,
                            reload_macro=reload_macro) }}
makina-mysql-service-reload-r:
  mc_proxy.hook: []
  cmd.wait:
    - name: service mysql reload
    {# workaround for Failed to reload mysql.service: Job type reload is not applicable for unit mysql.service.
     systemctl reload mysql wont work
     service mysql reload works
    #}
    - watch:
      - mc_proxy: makina-mysql-service-reload-r
      - mc_proxy: mysql-pre-restart-hook
      - mc_proxy: ssl-certs-end
    - watch_in:
      - mc_proxy: mysql-post-restart-hook
{% endif %}

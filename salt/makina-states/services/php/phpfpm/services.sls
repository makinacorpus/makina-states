{%- import "makina-states/_macros/h.jinja" as h with context %}
{% set phpSettings = salt['mc_php.settings']() %}
{%- set pm = salt['mc_services_managers.get_processes_manager'](phpSettings) %}
{%- set service_function = salt['mc_services_managers.get_service_function'](pm) %}
include:
  - makina-states.services.php.hooks

{% if service_function %}
{% macro restart_macro() %}
    - watch:
      # restart service in case of package install
      - mc_proxy: makina-php-pre-restart
    - require_in:
      # restart service in case of package install
      - mc_proxy: makina-php-post-restart
{% endmacro %}
{{ h.service_restart_reload(phpSettings.service,
                            service_function=service_function,
                            pref='makina-phpfpm',
                            restart_macro=restart_macro,
                            reload=False) }}
{% endif %}

# In most cases graceful reloads should be enough
{# has problem with reload for now
fpm-makina-php-reload:
  service.running:
    - name: {{ phpSettings.service }}
    - watch:
      # reload service in case of package install
      - mc_proxy: makina-php-pre-restart
    - require_in:
      # reload service in case of package install
      - mc_proxy: makina-php-post-restart
    - enable: True
    # does not work pretty well, use complete restart - reload: True
#}

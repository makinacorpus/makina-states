{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set data = salt['mc_ulogd.settings']() %}
include:
  - makina-states.services.log.ulogd.hooks
{# we do not start anymore by default ulogd on containers #}
{% if data.get('enabled', True) %}%}
makina-ulogd-restart-service:
  service.running:
    - name: {{data.service_name}}
    - enable: true
    - watch:
      - mc_proxy: ulogd-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: ulogd-post-hardrestart-hook
{% else %}
makina-ulogd-restart-service:
  service.dead:
    - name: {{data.service_name}}
    - enable: false
    - watch:
      - mc_proxy: ulogd-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: ulogd-post-hardrestart-hook
{% endif %}
{%endif%}

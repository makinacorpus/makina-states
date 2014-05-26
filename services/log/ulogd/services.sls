{% if salt['mc_controllers.mastersalt_mode']() %}
{% set data = salt['mc_ulogd.settings']() %}
include:
  - makina-states.services.log.ulogd.hooks

makina-ulogd-service:
  service.running:
    - name: {{data.service_name}}
    - enable: true
    - reload: true
    - watch:
      - mc_proxy: ulogd-pre-restart-hook
    - watch_in:
      - mc_proxy: ulogd-post-restart-hook

makina-ulogd-restart-service:
  service.running:
    - name: {{data.service_name}}
    - enable: true
    - watch:
      - mc_proxy: ulogd-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: ulogd-post-hardrestart-hook
{%endif%}

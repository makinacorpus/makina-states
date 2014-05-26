include:
  - makina-states.services.log.ulogd.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
{% set name = "ulogd" %}
{% if grains['os'] in ['Ubuntu'] %}
{% set name = "ulogd2" %}
{% endif %}

makina-ulogd-service:
  service.running:
    - name: {{name}}
    - enable: true
    - reload: true
    - watch:
      - mc_proxy: ulogd-pre-restart-hook
    - watch_in:
      - mc_proxy: ulogd-post-restart-hook

makina-ulogd-restart-service:
  service.running:
    - name: {{name}}
    - enable: true
    - watch:
      - mc_proxy: ulogd-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: ulogd-post-hardrestart-hook
{%endif%}

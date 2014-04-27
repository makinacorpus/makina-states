include:
  - makina-states.services.log.rsyslog.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}

makina-rsyslog-service:
  service.running:
    - name: rsyslog
    - enable: true
    - reload: true
    - watch:
      - mc_proxy: rsyslog-pre-restart-hook
    - watch_in:
      - mc_proxy: rsyslog-post-restart-hook

makina-rsyslog-restart-service:
  service.running:
    - name: rsyslog
    - enable: true
    - watch:
      - mc_proxy: rsyslog-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: rsyslog-post-hardrestart-hook
{%endif%}

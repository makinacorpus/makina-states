include:
  - makina-states.services.log.rsyslog.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
makina-rsyslog-restart-service:
  service.running:
    - name: rsyslog
    - enable: true
    - watch:
      - mc_proxy: rsyslog-pre-restart-hook
      - mc_proxy: rsyslog-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: rsyslog-post-restart-hook
      - mc_proxy: rsyslog-post-hardrestart-hook
{%endif%}

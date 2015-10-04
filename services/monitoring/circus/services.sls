include:
  - makina-states.services.monitoring.circus.hooks
  - makina-states.services.base.cron
  {% if salt['mc_nodetypes.is_docker']() %}
  - makina-states.services.base.cron.service
  - makina-states.services.log.rsyslog.services
  {% endif %}

{% if not salt['mc_nodetypes.is_docker']() %}
circus-start:
  service.running:
    - name: circusd
    - enable: True
    - watch:
      - mc_proxy: circus-pre-restart
    - watch_in:
      - mc_proxy: circus-post-restart
{% endif %}

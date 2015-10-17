include:
  - makina-states.services.monitoring.circus.hooks
  - makina-states.services.base.cron
  {% if salt['mc_nodetypes.activate_sysadmin_states']()%}
  - makina-states.services.base.ssh.services
  - makina-states.services.base.cron.service
  - makina-states.services.log.rsyslog.services
  - makina-states.services.firewall.fail2ban.services
  {% endif %}
{% if salt['mc_nodetypes.activate_sysadmin_states']() and not salt['mc_nodetypes.is_docker_service']() %}
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
{% endif %}

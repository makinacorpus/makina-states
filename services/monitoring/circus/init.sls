{{- salt['mc_macros.register']('services', 'monitoring.circus') }}
include:
  - makina-states.services.monitoring.circus.prerequisites
  - makina-states.services.monitoring.circus.configuration
  - makina-states.services.monitoring.circus.services
  {% if salt['mc_nodetypes.is_docker_service']()%}
  - makina-states.services.base.ssh
  - makina-states.services.base.cron
  - makina-states.services.log.rsyslog
  - makina-states.services.firewall.fail2ban
  {% endif %}

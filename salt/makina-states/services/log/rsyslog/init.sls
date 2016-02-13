{{ salt['mc_macros.register']('services', 'log.rsyslog') }}
include:
  - makina-states.services.log.rsyslog.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() or (
salt['mc_nodetypes.is_docker']() and not salt['mc_controllers.allow_lowlevel_states']()) %}
  - makina-states.services.log.rsyslog.prerequisites
  - makina-states.services.log.rsyslog.configuration
  - makina-states.services.log.rsyslog.services
{%endif%}

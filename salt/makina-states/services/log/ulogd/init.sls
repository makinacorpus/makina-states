{{ salt['mc_macros.register']('services', 'log.ulogd') }}
include:
  - makina-states.services.log.ulogd.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.services.log.ulogd.prerequisites
  - makina-states.services.log.ulogd.configuration
  - makina-states.services.log.ulogd.services
{%endif%}

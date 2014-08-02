{% if salt['mc_controllers.allow_lowlevel_states']() %}
include:
  - makina-states.services_managers.system.hooks
  - makina-states.services_managers.system.unregister
{%endif %}

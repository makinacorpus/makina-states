{% if salt['mc_controllers.allow_lowlevel_states']() %}
include:
  - makina-states.services.virt.virtualbox.hooks
{% endif %}

{% if salt['mc_controllers.mastersalt_mode']() %}
include:
  - makina-states.services.virt.virtualbox.hooks
{% endif %}

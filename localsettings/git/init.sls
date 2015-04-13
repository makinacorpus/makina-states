include:
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.localsettings.git.configuration
{% endif %}
  - makina-states.localsettings.git.hooks

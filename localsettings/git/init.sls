include:
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.localsettings.git.configuration
{% endif %}
  - makina-states.localsettings.git.hooks

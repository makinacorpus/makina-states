include:
  - makina-states.localsettings.apparmor.hooks

{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% if grains['os'] in ['Ubuntu'] %}
{% endif %}
{% endif %}

include:
  - makina-states.localsettings.apparmor.hooks

{% if salt['mc_controllers.mastersalt_mode']() %}
{% if grains['os'] in ['Ubuntu'] %}
{% endif %}
{% endif %}

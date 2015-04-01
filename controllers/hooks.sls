include:
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.controllers.mastersalt-hooks
{% else %}
  - makina-states.controllers.salt-hooks
{% endif %}

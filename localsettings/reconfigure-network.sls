ms-reconfigure-network:
  mc_proxy.hook: []

{% if salt['mc_localsettings.registry']()['has']['network'] %}
include:
  - makina-states.localsettings.network
{% endif %}

{# see makina-states.services.standalone #}
include:
  - makina-states.services.standalone
  - makina-states.common.autocommit
  {% if salt['mc_nodetypes.is_docker']() %}
  - makina-states.services.base.ssh.rootkey
  {% endif %}

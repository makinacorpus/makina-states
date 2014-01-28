{#-
#
# Extra setup for a virtual machine running on a bare metal server
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ salt['mc_macros.register']('nodetypes', 'vm') }}
include:
  - makina-states.nodetypes.server

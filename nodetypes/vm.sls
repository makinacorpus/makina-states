{#-
#
# Extra setup for a virtual machine running on a bare metal server
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ nodetypes.register('vm') }}
include:
  - {{ nodetypes.statesPref }}server

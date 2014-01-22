{#
# extra setup on a docker container
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ nodetypes.register('dockercontainer') }}

include:
  - {{ nodetypes.statesPref }}lxccontainer

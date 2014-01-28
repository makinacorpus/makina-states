{#
# extra setup on a docker container
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ salt['mc_macros.register']('nodetypes', 'dockercontainer') }}

include:
  - makina-states.nodetypes.lxccontainer

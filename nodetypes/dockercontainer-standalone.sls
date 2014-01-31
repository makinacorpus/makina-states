{#
# Flag the machine as a docker container
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ salt['mc_macros.register']('nodetypes', 'dockercontainer') }}


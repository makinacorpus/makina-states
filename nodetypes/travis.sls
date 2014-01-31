{#
# Setup for makina/vms travis test box
#
# only nuance for now is to disable sysctls in salt macro
#
#}

{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{{ salt['mc_macros.register']('nodetypes', 'travis') }}
{% set localsettings = nodetypes.localsettings %}

include:
  - makina-states.nodetypes.devhost

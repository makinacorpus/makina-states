{#-
# Flag the machine as a development box
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/vm.rst
#}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'vm') }}
{% if full %}
include:
  - makina-states.nodetypes.server
{% endif %}
{% endmacro %}
{{do(full=False)}}

{#-
# Flag the machine as a development box
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/kvm.rst
#}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'kvm') }}
{% if full %}
include:
  - makina-states.nodetypes.vm
{% endif %}
{% endmacro %}
{{do(full=False)}}

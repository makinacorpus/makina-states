{#
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/server.rst
#}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'scratch') }}
ms-scratch-dummy-{{full}}:
  mc_proxy.hook: [] 
{% endmacro %}
{{do(full=False)}}


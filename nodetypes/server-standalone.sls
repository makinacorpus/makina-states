{#
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/server.rst
#}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'server') }}
{% if full %}
include:
  - makina-states.localsettings
{% endif %}
{% endmacro %}
{{do(full=False)}}

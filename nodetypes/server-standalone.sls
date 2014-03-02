{#
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/server.rst
#}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'server') }}
{% if full %}
include:
  - makina-states.localsettings
{% endif %}
{% endmacro %}
{{do(full=False)}}

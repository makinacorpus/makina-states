# to install makina-states without much configuration
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'server') }}
{% if full %}
include:
  - makina-states.nodetypes.scratch
  - makina-states.localsettings
{% endif %}
{% endmacro %}
{{do(full=False)}}

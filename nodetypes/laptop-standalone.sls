{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'laptop') }}
{% if full %}
include:
  - makina-states.localsettings
{% endif %}
{% endmacro %}
{{do(full=False)}}

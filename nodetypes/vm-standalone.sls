{# Extra setup for a virtual machine running on a bare metal server #}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'vm') }}
{% if full %}
include:
  - makina-states.nodetypes.server
{% endif %}
{% endmacro %}
{{do(full=False)}}

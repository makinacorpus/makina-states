{# install server with enforcing local configuration
   to be sure makina-states will be happy #}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'server') }}
{% if full %}
include:
  - makina-states.nodetypes.scratch
  - makina-states.localsettings
{% endif %}
{% endmacro %}
{{do(full=False)}}

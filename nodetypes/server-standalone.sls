{# install server with enforcing local configuration
   to be sure makina-states will be happy #}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('nodetypes', 'server') }}
{% if full %}
include:
  - makina-states.nodetypes.scratch
  - makina-states.localsettings
  {% if not salt['mc_nodetypes.is_devhost']() %}
  - makina-states.localsettings.check_raid
  {% endif %}
{% endif %}
{% endmacro %}
{{do(full=False)}}

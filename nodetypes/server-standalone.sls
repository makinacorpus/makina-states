{#-
# Boostrap an host:
#   - install base packages & settings like (non exhaustive):
#     - configure editor
#     - configure shell
#     - configure sudoers
#     - configure base users
#     - configure ldap if enabled
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

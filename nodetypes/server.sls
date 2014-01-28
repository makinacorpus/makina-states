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
{{ salt['mc_macros.register']('nodetypes', 'server') }}
include:
  - makina-states.localsettings

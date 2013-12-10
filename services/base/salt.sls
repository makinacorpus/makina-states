#
# Install a minion for makina-states tree in normal mode
#

include:
  - makina-states.services.base.salt_base
{% import "makina-states/_macros/salt.jinja" as c with context %}
{{ c.install_makina_states_minion(c.saltname)}}

#
# Install a minion for makina-states tree in mastersalt mode
#

{% import "makina-states/_macros/salt.jinja" as c with context %}
include:
  - makina-states.services.base.mastersalt_base

{{ c.install_makina_states_minion(c.msaltname)}}

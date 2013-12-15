#
# Install a master for makina-states tree in mastersalt mode
#

{% import "makina-states/_macros/salt.jinja" as c with context %}

include:
  - makina-states.services.base.mastersalt

{{ c.install_makina_states_master(c.msaltname)}}

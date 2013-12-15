#
# Install a master for makina-states tree in normal mode
#
{% import "makina-states/_macros/salt.jinja" as c with context %}

include:
  - makina-states.services.base.salt

{{ c.install_makina_states_master(c.saltname)}}

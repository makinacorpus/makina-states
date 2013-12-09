{% import "makina-states/_macros/salt.jinja" as c with context %}

include:
  - makina-states.services.base.salt

{{ set name='salt' }}
{{ set mode='salt' }}
{{ install_makina_states_master(name, mode)}}
